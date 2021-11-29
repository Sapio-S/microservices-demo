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
import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
# from kubernetes import client, config
# from const_dic import *
from consts import consts
# constants
max_retry = 5
services = ["adservice", "cartservice", "checkoutservice", "currencyservice", "emailservice", "frontend", "paymentservice", "productcatalogservice", "recommendationservice", "redis", "shippingservice"]
ops = ["get", "set"]
token = "2kmAK9DbfrhFA-nojNc1DKk3q8wQ4a14SnmMdVOjvBfsgTH_saoqvCUaZXuW3CBMyW2tIlew-zud2p6jKSboPg=="
org = "msra"
bucket = "trace"
influxclient = InfluxDBClient(url="http://10.0.0.51:8086", token=token)
quantile = ["0.50", '0.90', '0.95', '0.99']
headers = ["service", "rps","avg", "0.50", '0.90', '0.95', '0.99']

def query_db(start_time, end_time, duration):
    start_time = start_time.astimezone().isoformat()
    end_time = end_time.astimezone().isoformat()
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

    return data

def change2csv(data, i, total_row):
    rows = services.copy()
    row_data = []
    for k, v in data.items():
        this_row = [k]
        for _, item in v.items():
            this_row.append(item)
        row_data.append(this_row)
    with open('res2/data'+str(i)+".csv", "w") as f:
        f_csv = csv.writer(f)
        f_csv.writerow(headers)
        f_csv.writerows(row_data)
        f_csv.writerow(total_row)

def export_data(data, i):
    total_row = ["total"]
    with open('wrk_table/232')as f:
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

def get(start_time, end_time):
    start_time = start_time.astimezone().isoformat()
    end_time = end_time.astimezone().isoformat()
    data90 = {}
    data50 = {}
    flag = False
    query = 'from(bucket: "trace") \
                |> range(start: {}, stop: {}) \
                |> filter(fn: (r) => r["_measurement"] == "service_metric" and r["_field"] == "latency") \
                |> group(columns: ["service"]) \
                |> toFloat() \
                |> quantile(q: {}, column:"_value") \
                '.format(start_time, end_time, "0.90")
    tables = influxclient.query_api().query(query, org=org)
    for table in tables:
        for record in table.records:
            flag = True
            service = record.values['service']
            data90[service] = record.values['_value']
    
    if not flag:
        return {}
    return data90

end_time = datetime.datetime.now(datetime.timezone.utc)
end_time = end_time.replace(hour=15, minute=32, second=00, day=21)
start_time = end_time.replace(hour=10, minute=0, second=0, day=21)
print("timezone", start_time, end_time)

cnt = 234
while end_time >= start_time:
    end_ = end_time - datetime.timedelta(seconds=10)
    data = get(end_, end_time)
    if len(data) == 0:
        end_time = end_    
    else: # data exist in [end_, end_time], start query
        end_ = end_time - datetime.timedelta(minutes=6)
        print(cnt, end_, end_time)
        data = query_db(end_, end_time, 300) # for 5 min
        # 生成报表，导出
        export_data(data, cnt)
        cnt += 1
        end_time = end_

