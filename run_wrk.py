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

from consts import consts
# constants
max_retry = 5
services = ["adservice", "cartservice", "checkoutservice", "currencyservice", "emailservice", "frontend", "paymentservice", "productcatalogservice", "recommendationservice", "redis", "shippingservice"]
ops = ["get", "set"]
token = "_CEHxF2nWxvPE6BW_qJvmXU2OCfnIcys3mm4mnivqpBb9VeBDnFsVi7f2M_YIgSREJAQBP8YQF2o7tRQF7ilHg=="
org = "msra"
bucket = "trace"
influxclient = InfluxDBClient(url="http://10.0.0.41:8086", token=token, org=org,timeout=300000)
# influxclient = InfluxDBClient(url="http://10.0.0.33:8086", token=token)

quantile = ["0.50", '0.90', '0.95', '0.99']

headers = ["service", "rps","avg", "0.50", '0.90', '0.95', '0.99']

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
        possible_para = consts[service]
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
    np.save("res/param_"+str(num_samples), para_dic)

# def read_parameters():
#     para_dic = np.load("res/param_300.npy", allow_pickle=True).item()

def read_parameters():
    global para_dic
    para_dic = np.load("res/param_100.npy", allow_pickle=True).item()

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
    
    # # get rps of recommendation pods
    # query = 'from(bucket: "trace") \
    #     |> range(start: {}, stop: {}) \
    #     |> filter(fn: (r) => r["_measurement"] == "service_metric" and r["_field"] == "latency" and r["service"] == "recommendationservice") \
    #     |> group(columns: ["op"]) \
    #     |> count() \
    #     '.format(start_time, end_time)
    # tables = influxclient.query_api().query(query, org=org)
    # for table in tables:
    #     for record in table.records:
    #         service = record.values['op']
    #         if service is None:
    #             continue
    #         try:
    #             data[service]["rps"] = float(record.values['_value'] / duration)
    #         except:
    #             data[service]["rps"] = 0

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
    
    # # get rps of checkout pods
    # query = 'from(bucket: "trace") \
    #     |> range(start: {}, stop: {}) \
    #     |> filter(fn: (r) => r["_measurement"] == "service_metric" and r["_field"] == "latency" and r["service"] == "checkoutservice") \
    #     |> group(columns: ["op"]) \
    #     |> count() \
    #     '.format(start_time, end_time)
    # tables = influxclient.query_api().query(query, org=org)
    # for table in tables:
    #     for record in table.records:
    #         service = record.values['op']
    #         if service is None:
    #             continue
    #         try:
    #             data[service]["rps"] = float(record.values['_value'] / duration)
    #         except:
    #             data[service]["rps"] = 0

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
    
    # pod_name = {}
    # cnt = 0
    # # get rps of recommendation pods
    # query = 'from(bucket: "trace") \
    #     |> range(start: {}, stop: {}) \
    #     |> filter(fn: (r) => r["_measurement"] == "service_metric" and r["_field"] == "latency" and r["service"] == "recommendationservice") \
    #     |> group(columns: ["podname"]) \
    #     |> count() \
    #     '.format(start_time, end_time)
    # tables = influxclient.query_api().query(query, org=org)
    # for table in tables:
    #     for record in table.records:
    #         service = record.values['podname']
    #         if service is None:
    #             continue
    #         if service not in pod_name:
    #             pod_name[service] = cnt
    #             data["recommendation_pod"+str(pod_name[service])] = {}
    #             cnt += 1
    #         try:
    #             data["recommendation_pod"+str(pod_name[service])]["rps"] = float(record.values['_value'] / duration)
    #         except:
    #             data["recommendation_pod"+str(pod_name[service])]["rps"] = 0
    
    # # get p50, p75, p90, p99 latency of recommendation pods
    # for q in quantile:
    #     query = 'from(bucket: "trace") \
    #         |> range(start: {}, stop: {}) \
    #         |> filter(fn: (r) => r["_measurement"] == "service_metric" and r["_field"] == "latency" and r["service"] == "recommendationservice") \
    #         |> group(columns: ["podname"]) \
    #         |> toFloat() \
    #         |> quantile(q: {}, column: "_value") \
    #         '.format(start_time, end_time, q)
    #     tables = influxclient.query_api().query(query, org=org)
    #     for table in tables:
    #         for record in table.records:
    #             service = record.values['podname']
    #             if service is None:
    #                 continue
    #             data["recommendation_pod"+str(pod_name[service])][q] = record.values['_value']
    
    # pod_name = {}
    # cnt = 0
    # # get rps of checkout pods
    # query = 'from(bucket: "trace") \
    #     |> range(start: {}, stop: {}) \
    #     |> filter(fn: (r) => r["_measurement"] == "service_metric" and r["_field"] == "latency" and r["service"] == "checkoutservice") \
    #     |> group(columns: ["podname"]) \
    #     |> count() \
    #     '.format(start_time, end_time)
    # tables = influxclient.query_api().query(query, org=org)
    # for table in tables:
    #     for record in table.records:
    #         service = record.values['podname']
    #         if service is None:
    #             continue
    #         if service not in pod_name:
    #             pod_name[service] = cnt
    #             data["checkout_pod"+str(pod_name[service])] = {}
    #             cnt += 1
    #         try:
    #             data["checkout_pod"+str(pod_name[service])]["rps"] = float(record.values['_value'] / duration)
    #         except:
    #             data["checkout_pod"+str(pod_name[service])]["rps"] = 0
    
    # # get p50, p75, p90, p99 latency of checkout pods
    # for q in quantile:
    #     query = 'from(bucket: "trace") \
    #         |> range(start: {}, stop: {}) \
    #         |> filter(fn: (r) => r["_measurement"] == "service_metric" and r["_field"] == "latency" and r["service"] == "checkoutservice") \
    #         |> group(columns: ["podname"]) \
    #         |> toFloat() \
    #         |> quantile(q: {}, column: "_value") \
    #         '.format(start_time, end_time, q)
    #     tables = influxclient.query_api().query(query, org=org)
    #     for table in tables:
    #         for record in table.records:
    #             service = record.values['podname']
    #             if service is None:
    #                 continue
    #             data["checkout_pod"+str(pod_name[service])][q] = record.values['_value']
    return data


def change2csv(data, i, total_row):
    rows = services.copy()
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
        f_csv.writerow(total_row)

def export_data(data, i):
    total_row = ["total"]
    with open('wrk_table/'+str(i))as f:
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


def run_one_set(i):
    '''
    测试一组参数，并收集数据
    '''
    print("collecting data of parameter set", i)
    generate_yaml(i)

    # 部署服务
    print("deploying...")
    retry = 0
    skaffold_run = subprocess.Popen("skaffold run --default-repo=sapiosss", 
        shell=True, stdout=subprocess.DEVNULL, stderr=sys.stderr)
    ret_code = skaffold_run.wait()
    while ret_code != 0:
        print("deployment failed. return code is "+str(ret_code)+" Retry. ")
        skaffold_run = subprocess.Popen("skaffold run --default-repo=sapiosss", 
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
    wrk_cmd = "/home/yuqingxie/wrk2/wrk -t5 -L -c10 -d5m --timeout 10s -s /home/yuqingxie/microservices-demo/wrk/script.lua -R150 " + ip
    print(wrk_cmd)
    wrk_record = open("wrk_table/"+str(i), mode="w")
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
    print("\n\n\n\n")
    return start_time, end_time

def generate_wrk():
    former = np.random.random() / 20 * 3 + 0.8 # [0.8, 0.95]
    add2cart_ratio = np.random.random() * (1 - former)

    index_ratio = np.random.random() / 10 # [0, 0.1]
    setCurrency_ratio = np.random.random() / 5 # [0, 0,2]
    browseProduct_ratio = np.random.random() / 2 + 0.25 # [0.25, 0.75]
    viewCart_ratio = np.random.random() / 3 # [0, 0.33]
    s = index_ratio+setCurrency_ratio+browseProduct_ratio+viewCart_ratio
    index_ratio = index_ratio * former / s
    setCurrency_ratio = setCurrency_ratio* former / s
    browseProduct_ratio = browseProduct_ratio* former / s
    viewCart_ratio = viewCart_ratio* former / s

    env = jinja2.Environment(loader=jinja2.FileSystemLoader("wrk"))
    temp = env.get_template("script.lua.tpl")
    temp_out = temp.render(
        index_ratio=index_ratio,
        setCurrency_ratio=setCurrency_ratio,
        browseProduct_ratio=browseProduct_ratio,
        viewCart_ratio=viewCart_ratio,
        add2cart_ratio=add2cart_ratio,
        )
    with open("wrk/generated-script.lua", 'w') as f:
        f.writelines(temp_out)
        f.close()
    
    return index_ratio, setCurrency_ratio, browseProduct_ratio, viewCart_ratio, add2cart_ratio

def main():
    num_samples = 120
    generate_parameters(num_samples)
    # read_parameters()
    print("generated parameters for", num_samples, "groups!")
    time_zone = []
    # wrk_para = []
    for i in range(num_samples):
        # if i <= 3:
        #     continue
        # index_ratio, setCurrency_ratio, browseProduct_ratio, viewCart_ratio, add2cart_ratio = generate_wrk()
        # wrk_para.append([index_ratio, setCurrency_ratio, browseProduct_ratio, viewCart_ratio, add2cart_ratio])
        start,end = run_one_set(i)
        time_zone.append([start, end])
    np.save("res/time_zone", time_zone)
    # np.save("res/wrk_para", wrk_para)

main()