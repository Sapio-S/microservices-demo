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

# constants
max_retry = 5

services = ["adservice", "cartservice", "checkoutservice", "currencyservice", "emailservice", "frontend", "paymentservice", "productcatalogservice", "recommendationservice", "redis", "shippingservice"]
ops = ["get", "set"]

token = "b-M3xpZbjd9kVVf8DlQ8hAlAwc-ttyn12Ewhh1evVg7034k330Ox1PRIBHiuZ5Pum8g56Cjt-pD-s36UNg8JjQ=="
org = "msra"
bucket = "trace"
influxclient = InfluxDBClient(url="http://10.0.0.29:8086", token=token, org=org)

quantile = ["0.50", '0.90', '0.95', '0.99']

headers = ["service", "rps","avg", "0.50", '0.90', '0.95', '0.99']

def generate_yaml(param):
    '''
    填充参数，生成对应的yaml文件
    '''
    para_dict = {}
    for service in services:
        para_dict[service] = {}
        for k in param.keys():
            try:
                if k[:len(service)]==service:
                    para_dict[service][k[len(service)+1:]] = int(param[k])
                elif k[:3]=="get":
                    if k[4]=='h' or k[4]=='m':
                        para_dict["cartservice"][k[4:]] = int(param["get"+k[3:]])
                    else:
                        para_dict["redis"][k[4:]] = int(param["get"+k[3:]])
            except:
                continue
    for service in services:
        para=para_dict[service]
        # print(service, para)
        env = jinja2.Environment(loader=jinja2.FileSystemLoader("kubernetes-manifests-tpl"))
        temp = env.get_template(service+".yaml.tpl")
        temp_out = temp.render(para=para)
        with open(os.path.join("generated-manifests", service+'.yaml'), 'w') as f:
            f.writelines(temp_out)
            f.close()

def print_cmd(p):
    # 实时打印子进程的执行结果
    while p.poll() is None:
        line = p.stdout.readline()
        line = line.strip()
        if line:
            print(line)

def get_ip():
    # 此函数用来获取k8s部署中cluster IP
    get_ip = subprocess.Popen("kubectl get svc frontend", shell=True, stdout=subprocess.PIPE, stderr=sys.stderr)
    get_ip.wait()
    output = get_ip.stdout.read()
    ip = re.search(r'.* (10.*?) .*', str(output))
    port = re.search(r'.*  (.*?)/TCP', str(output))
    return "http://" + ip.group(1) + ":" + port.group(1)

def query_db(start_time, end_time, duration):
    data = {}
    # generate service & DB keys
    for service in services:
        data[service] = {}
    for op in ops:
        data[op] = {}

    # get rps of a service
    query = 'from(bucket: "trace") \
        |> range(start: {}, stop: {}) \
        |> filter(fn: (r) => r["_measurement"] == "service_metric" and r["_field"] == "latency") \
        |> group(columns: ["service"]) \
        |> count() \
        '.format(start_time, end_time)
    tables = influxclient.query_api().query(query, org=org)
    for table in tables:
        for record in table.records:
            service = record.values['service']
            data[service]["rps"] = float(record.values['_value'] / duration)
    
    # get average latency of a service
    query = 'from(bucket: "trace") \
        |> range(start: {}, stop: {}) \
        |> filter(fn: (r) => r["_measurement"] == "service_metric" and r["_field"] == "latency") \
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
    query = 'from(bucket: "trace") \
        |> range(start: {}, stop: {}) \
        |> filter(fn: (r) => r["_measurement"] == "service_metric" and r["_field"] == "latency" and r["service"] == "cartservice") \
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
    query = 'from(bucket: "trace") \
        |> range(start: {}, stop: {}) \
        |> filter(fn: (r) => r["_measurement"] == "service_metric" and r["_field"] == "latency" and r["service"] == "cartservice") \
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
            |> filter(fn: (r) => r["_measurement"] == "service_metric" and r["_field"] == "latency") \
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
            |> filter(fn: (r) => r["_measurement"] == "service_metric" and r["_field"] == "latency" and r["service"] == "cartservice") \
            |> group(columns: ["op"]) \
            |> toFloat() \
            |> quantile(q: {}, column: "_value") \
            '.format(start_time, end_time, q)
        tables = influxclient.query_api().query(query, org=org)
        for table in tables:
            for record in table.records:
                service = record.values['op']
                data[service][q] = record.values['_value']
    
    # get rps of checkout pods
    query = 'from(bucket: "trace") \
        |> range(start: {}, stop: {}) \
        |> filter(fn: (r) => r["_measurement"] == "service_metric" and r["_field"] == "latency" and r["service"] == "checkoutservice") \
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
    
    pod_name = {}
    cnt = 0
    # get rps of checkout pods
    query = 'from(bucket: "trace") \
        |> range(start: {}, stop: {}) \
        |> filter(fn: (r) => r["_measurement"] == "service_metric" and r["_field"] == "latency" and r["service"] == "checkoutservice") \
        |> group(columns: ["podname"]) \
        |> count() \
        '.format(start_time, end_time)
    tables = influxclient.query_api().query(query, org=org)
    for table in tables:
        for record in table.records:
            service = record.values['podname']
            if service is None:
                continue
            if service not in pod_name:
                pod_name[service] = cnt
                data["checkout_pod"+str(pod_name[service])] = {}
                cnt += 1
            try:
                data["checkout_pod"+str(pod_name[service])]["rps"] = float(record.values['_value'] / duration)
            except:
                data["checkout_pod"+str(pod_name[service])]["rps"] = 0
    
    # get p50, p75, p90, p99 latency of checkout pods
    for q in quantile:
        query = 'from(bucket: "trace") \
            |> range(start: {}, stop: {}) \
            |> filter(fn: (r) => r["_measurement"] == "service_metric" and r["_field"] == "latency" and r["service"] == "checkoutservice") \
            |> group(columns: ["podname"]) \
            |> toFloat() \
            |> quantile(q: {}, column: "_value") \
            '.format(start_time, end_time, q)
        tables = influxclient.query_api().query(query, org=org)
        for table in tables:
            for record in table.records:
                service = record.values['podname']
                if service is None:
                    continue
                data["checkout_pod"+str(pod_name[service])][q] = record.values['_value']
    return data

def change2csv(data, i, total_row):
    rows = services.copy()
    row_data = []
    for k, v in data.items():
        this_row = [k]
        for _, item in v.items():
            this_row.append(item)
        row_data.append(this_row)
    with open('test_res/data'+str(i)+".csv", "w") as f:
        f_csv = csv.writer(f)
        f_csv.writerow(headers)
        f_csv.writerows(row_data)
        f_csv.writerow(total_row)

def export_data(data, i):
    total_row = ["total"]
    with open('test_res/'+i)as f:
        for line in f:
            sentence = line.split()
            if len(sentence) < 1:
                continue
            if sentence[0] == "Requests/sec:": # rps   
                total_row.insert(1, sentence[1])
            if sentence[0] == "Latency" and sentence[1] != "Distribution":  # "    Latency   674.61ms  542.39ms   2.00s    59.46%"
                total_row.append(sentence[1]) # avg
            if sentence[0] == "50.000%":
                total_row.append(sentence[1]) # p50
            if sentence[0] == "90.000%":
                total_row.append(sentence[1]) # p90
            if sentence[0] == "95.000%":
                total_row.append(sentence[1]) # p95
            if sentence[0] == "99.000%":
                total_row.append(sentence[1]) # p99
    change2csv(data, i, total_row)


def run_one_set(i, param):
    '''
    测试一组参数，并收集数据
    '''
    print("collecting data of parameter set", i)
    generate_yaml(param)

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
    ip = get_ip()
    time.sleep(5)
    wrk_cmd = "/home/yuqingxie/wrk2/wrk -t5 -L -c50 -d5m --timeout 10s -s /home/yuqingxie/microservices-demo/wrk/script.lua -R145 " + ip
    print(wrk_cmd)
    wrk_record = open("test_res/"+i, mode="w")
    wrk_run = subprocess.Popen(wrk_cmd, shell=True, stdout=wrk_record, stderr=sys.stderr)
    ret_code = wrk_run.wait()
    print("wrk exited with code ", ret_code)
    wrk_record.close()

    # 清除当前的部署，触发service中的数据上传
    print("cleaning deployment...")
    skaffold_delete = subprocess.Popen("skaffold delete", shell=True, stdout=subprocess.DEVNULL, stderr=sys.stderr)
    skaffold_delete.wait()
    
    end_time = datetime.now(timezone.utc).astimezone().isoformat() # 用来查询influxDB中压测时间段内生成的数据

    # 从influxDB中获取各个服务的latency与rps
    start_query = time.time()
    data = query_db(start_time, end_time, 300) # for 5 min
    end_query = time.time()
    print("query takes", end_query - start_query, "seconds")

    # 生成报表，导出
    export_data(data, i)

    print("finished tested parameter set", i)
    print("\n\n")
    return start_time, end_time

def main():
    time_zone = []

    # fluxion_files = []
    fluxion_files = []
    total_files = []

    for train in [10,25,50,100]:
        for i in range(10):
            # name = "DNN_2checkout_"+str(train)+"_"+str(i)
            # total_files.append(["1116/"+str(name)+".npy", name])
            name = "fluxion_single_"+str(train)+"_"+str(i)
            total_files.append(["1128_2/"+str(name)+".npy", name])            
            name = "GP_single_"+str(train)+"_"+str(i)
            total_files.append(["1128_2/"+str(name)+".npy", name])
    # total_files.append(["1116/"+str(name)+".npy", name])
    
    for files in total_files:
        param = np.load(files[0], allow_pickle = True).item()
        start,end = run_one_set(files[1], param)
        time_zone.append([start, end])

main()