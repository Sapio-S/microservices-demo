import jinja2
import sys
import os
import subprocess
import re
import time
import numpy as np
import csv
import random
import yaml
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
# from kubernetes import client, config

from consts import const_dic
# constants
max_retry = 5

services = ["adservice", "cartservice", "checkoutservice", "currencyservice", "emailservice", "frontend", "paymentservice", "productcatalogservice", "recommendationservice", "redis", "shippingservice"]
ops = ["get", "set"]

token = "2kmAK9DbfrhFA-nojNc1DKk3q8wQ4a14SnmMdVOjvBfsgTH_saoqvCUaZXuW3CBMyW2tIlew-zud2p6jKSboPg=="
org = "msra"
bucket = "trace"
influxclient = InfluxDBClient(url="http://10.0.0.51:8086", token=token)

quantile = ["0.50", '0.75', '0.90', '0.99']

headers = ["service", "rps","avg", "0.50", '0.75', '0.90', '0.99']

# global variables
para_dic = {} # 参数配置，以service为基本单元

def generate_yaml(epoch):
    '''
    填充参数，生成对应的yaml文件
    '''
    for service in services:
        para=para_dic[service][epoch]
        env = jinja2.Environment(loader=jinja2.FileSystemLoader("kubernetes-manifests-tpl"))
        temp = env.get_template(service+".yaml.tpl")
        temp_out = temp.render(para=para)
        with open(os.path.join("generated-manifests", service+'.yaml'), 'w') as f:
            f.writelines(temp_out)
            f.close()
    
    # 生成压力测试文件（locust）
    # env = jinja2.Environment(loader=jinja2.FileSystemLoader("src/loadgenerator"))
    # temp = env.get_template("locust.py.tpl")
    # temp_out = temp.render(para=para)
    # with open("src/loadgenerator/locust.py", 'w') as f:
    #     f.writelines(temp_out)
    #     f.close()

def sample_selection(num_samples, x_bounds):
    '''
    num_samples:取样区间个数
    x_bounds:array,表示每个变量的上下界, e.g.[[100, 600], [100, 600], [100, 600]]
    返回值：array, num_samples组参数，e.g. [[598, 287, 539], [339, 242, 466]]
    '''
    outputs = []

    sampled = []
    for i in range(len(x_bounds)):
        sampled.append([False] * num_samples)

    # Generate LHS random samples
    for i in range(0, num_samples):
        temp = [None] * len(x_bounds)
        for j in range(len(x_bounds)):
            idx = None
            while idx == None or sampled[j][idx] == True:
                idx = random.randint(0, num_samples - 1)  # Choose the interval to sample

            sampled[j][idx] = True  # Note that we have sampled this interval

            intervalSize = ((x_bounds[j][1] - x_bounds[j][0]) / num_samples)
            intervalLowerBound = int(x_bounds[j][0] + intervalSize * idx)
            intervalUpperBound = int(intervalLowerBound + intervalSize)
            # sample = random.uniform(intervalLowerBound, intervalUpperBound)
            sample = random.randint(intervalLowerBound, intervalUpperBound)  # Samples within the chosen interval
            temp[j] = sample
        outputs.append(temp)

    return outputs

def generate_parameters(num_samples):
    for service in services:
        possible_para = const_dic[service]
        boundaries = []
        header = []
        service_list = []
        for k, v in possible_para.items():
            header.append(k) # name of parameter, e.g. adservice-MAX_ADS_TO_SERVE
            boundaries.append([v["MIN"], v["MAX"]])
        params = sample_selection(num_samples, boundaries)
        for i in range(num_samples):
            service_dic = {}
            for j in range(len(header)):
                service_dic[header[j]] = params[i][j]
            service_list.append(service_dic)
        para_dic[service] = service_list
    np.save("res/param"+str(num_samples), para_dic)

def print_cmd(p):
    # 实时打印子进程的执行结果
    while p.poll() is None:
        line = p.stdout.readline()
        line = line.strip()
        if line:
            print(line)

def get_ip():
    # 更换部署后需要更改这个命令
    # 此函数用来获取minikube部署中得到的网址
    get_ip = subprocess.Popen("minikube service frontend-external", shell=True, stdout=subprocess.PIPE, stderr=sys.stderr)
    get_ip.wait()
    output = get_ip.stdout.read()
    objs = re.search(r'.* (http://.*?) .*', str(output))
    return objs.group(1)

def query_db(start_time, end_time, duration):
    data = {}
    # generate service & DB keys
    for service in services:
        data[service] = {}
    for op in ops:
        data[op] = {}

    # get rps of a service
    for q in quantile:
        query = 'from(bucket: "trace") \
            |> range(start: {}, stop: {}) \
            |> filter(fn: (r) => r["_measurement"] == "s" and r["_field"] == "latency") \
            |> group(columns: ["service"]) \
            |> count() \
            '.format(start_time, end_time)
        tables = influxclient.query_api().query(query, org=org)
        for table in tables:
            for record in table.records:
                service = record.values['service']
                data[service]["rps"] = float(record.values['_value'] / duration)
    
    # get average latency of a service
    for q in quantile:
        query = 'from(bucket: "trace") \
            |> range(start: {}, stop: {}) \
            |> filter(fn: (r) => r["_measurement"] == "s" and r["_field"] == "latency") \
            |> group(columns: ["service"]) \
            |> toFloat() \
            |> mean() \
            '.format(start_time, end_time)
        tables = influxclient.query_api().query(query, org=org)
        for table in tables:
            for record in table.records:
                service = record.values['service']
                data[service]["avg"] = record.values['_value']
    
    # get rps of redisDB
    for q in quantile:
        query = 'from(bucket: "trace") \
            |> range(start: {}, stop: {}) \
            |> filter(fn: (r) => r["_measurement"] == "s" and r["_field"] == "latency" and r["service"] == "cartservice") \
            |> group(columns: ["op"]) \
            |> count() \
            '.format(start_time, end_time)
        tables = influxclient.query_api().query(query, org=org)
        for table in tables:
            for record in table.records:
                service = record.values['op']
                if service is None:
                    continue
                try:
                    data[service]["rps"] = float(record.values['_value'] / duration)
                except:
                    data[service]["rps"] = 0
    
    # get average latency of redisDB
    for q in quantile:
        query = 'from(bucket: "trace") \
            |> range(start: {}, stop: {}) \
            |> filter(fn: (r) => r["_measurement"] == "s" and r["_field"] == "latency" and r["service"] == "cartservice") \
            |> group(columns: ["op"]) \
            |> toFloat() \
            |> mean() \
            '.format(start_time, end_time)
        tables = influxclient.query_api().query(query, org=org)
        for table in tables:
            for record in table.records:
                service = record.values['op']
                if service is None:
                    continue
                try:
                    data[service]["avg"] = record.values['_value']
                except:
                    data[service]["avg"] = 0

    # get p50, p75, p90, p99 latency of a service
    for q in quantile:
        query = 'from(bucket: "trace") \
            |> range(start: {}, stop: {}) \
            |> filter(fn: (r) => r["_measurement"] == "s" and r["_field"] == "latency") \
            |> group(columns: ["service"]) \
            |> toFloat() \
            |> quantile(q: {}, column: "_value") \
            '.format(start_time, end_time, q)
        tables = influxclient.query_api().query(query, org=org)
        for table in tables:
            for record in table.records:
                service = record.values['service']
                data[service][q] = record.values['_value']

    # get p50, p75, p90, p99 latency of redisDB
    for q in quantile:
        query = 'from(bucket: "trace") \
            |> range(start: {}, stop: {}) \
            |> filter(fn: (r) => r["_measurement"] == "s" and r["_field"] == "latency" and r["service"] == "cartservice") \
            |> group(columns: ["op"]) \
            |> toFloat() \
            |> quantile(q: {}, column: "_value") \
            '.format(start_time, end_time, q)
        tables = influxclient.query_api().query(query, org=org)
        for table in tables:
            for record in table.records:
                service = record.values['op']
                data[service][q] = record.values['_value']
    return data

def change2csv(data, i):
    rows = services.copy()
    rows.append("total")
    row_data = []
    for k, v in data.items():
        this_row = [k]
        for _, item in v.items():
            this_row.append(item)
        row_data.append(this_row)
    with open('res/data'+str(i)+".csv", "w") as f:
        f_csv = csv.writer(f)
        f_csv.writerow(headers)
        f_csv.writerows(row_data)

def export_data(data, i):
    data["total"] = {}
    with open('locust_table/'+str(i)+'_stats.csv')as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader]
        last_row = rows[-1]
        data["total"]["rps"] = float(last_row["Requests/s"])
        data["total"]["avg"] = float(last_row["Average Response Time"])
        data["total"]["0.50"] = float(last_row["50%"])
        data["total"]["0.75"] = float(last_row["75%"])
        data["total"]["0.90"] = float(last_row["90%"])
        data["total"]["0.99"] = float(last_row["99%"])
    # np.save("res/data"+str(i), data)
    para = {}
    for service in services:
        para[service] = para_dic[service][i]
    # np.save("res/param"+str(i), para)
    change2csv(data, i)
    # print(data)
    # print(para)

def run_one_set(i):
    '''
    测试一组参数，并收集数据
    '''
    print("collecting data of parameter set", i)
    generate_yaml(i)

    # 部署服务
    print("deploying...")
    retry = 0
    skaffold_run = subprocess.Popen("skaffold run --default-repo=sapios", 
        shell=True, stdout=subprocess.DEVNULL, stderr=sys.stderr)
    ret_code = skaffold_run.wait()
    while ret_code != 0:
        print("deployment failed. return code is "+str(ret_code)+" Retry. ")
        skaffold_run = subprocess.Popen("skaffold run --default-repo=sapios", 
            shell=True, stdout=subprocess.DEVNULL, stderr=sys.stderr)
        ret_code = skaffold_run.wait()
        retry += 1
        if retry > max_retry:
            sys.exit(1)
    print("successfully deployed!")

    start_time = datetime.now(timezone.utc).astimezone().isoformat() # 用来查询influxDB中压测时间段内生成的数据

    # 获取服务接口，进行压力测试
    # locust_ip = get_ip() # for minikube only
    expose_ip = subprocess.Popen("exec kubectl port-forward deployment/frontend 8080:8080", shell=True, stdout=subprocess.DEVNULL, stderr=sys.stderr)
    # while expose_ip.poll() is None:
    #     line = expose_ip.stdout.readline()
    #     line = line.strip()
    #     if line == b'Forwarding from [::1]:8080 -> 8080':
    #         print(line)
    #         break
    locust_cmd = "/home/yuqingxie/.local/bin/locust -u 200 -r 20 \
        -f src/loadgenerator/locustfile_original.py --headless \
        --run-time 5m --host http://10.0.0.51:8080 --csv=locust_table/"+str(i)
    print(locust_cmd)
    # start_timestamp = time.time() # 计算rps
    locust_run = subprocess.Popen(locust_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ret_code = locust_run.wait()
    print("locust exited with code ", ret_code)

    # 清除当前的部署，触发service中的数据上传
    print("cleaning deployment...")
    expose_ip.kill()
    # skaffold_delete = subprocess.Popen("skaffold delete", shell=True, stdout=subprocess.DEVNULL, stderr=sys.stderr)
    # skaffold_delete.wait()
    
    end_time = datetime.now(timezone.utc).astimezone().isoformat() # 用来查询influxDB中压测时间段内生成的数据
    # end_timestamp = time.time() # 计算rps

    # 从influxDB中获取各个服务的latency与rps
    # print(start_time, end_time)
    start_query = time.time()
    # print("time stamp diff is ", end_timestamp - start_timestamp)
    data = query_db(start_time, end_time, 300) # for 5 min
    end_query = time.time()
    print("query takes", end_query - start_query, "seconds")

    # 生成报表，导出
    export_data(data, i)

    # # 为了节省空间，清空locust_table文件夹
    # os.remove("locust_table")
    # os.mkdir("locust_table")

    print("finished tested parameter set", i)
    print("\n\n\n\n")

def main():
    num_samples = 1
    generate_parameters(num_samples)
    print("generated parameters for", num_samples, "groups!")
    for i in range(num_samples):
        run_one_set(i)

main()
