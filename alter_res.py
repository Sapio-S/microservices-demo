import time
import jinja2
import sys
import os
import subprocess
import re
import time
import numpy as np
import csv
import random
import datetime

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# You can generate a Token from the "Tokens Tab" in the UI
token = "_CEHxF2nWxvPE6BW_qJvmXU2OCfnIcys3mm4mnivqpBb9VeBDnFsVi7f2M_YIgSREJAQBP8YQF2o7tRQF7ilHg=="
org = "msra"
bucket = "trace"
influxclient = InfluxDBClient(url="http://10.0.0.41:8086", token=token, org=org)
quantile = ["0.90"]
# start_time = datetime.now(timezone.utc).astimezone().isoformat()
# end_time = datetime.now(timezone.utc).astimezone().isoformat()
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
def get_rps(start_time, end_time):
    for q in quantile:
        query = 'from(bucket: "trace") \
            |> range(start: {}, stop: {}) \
            |> filter(fn: (r) => r["_measurement"] == "service_metric" and r["_field"] == "latency" and r["service"] == "frontend") \
            |> count() \
            '.format(start_time, end_time)
        tables = influxclient.query_api().query(query, org=org)
        for table in tables:
            for record in table.records:
                service = record.values['op']
                if service is None:
                    continue
                try:
                    return float(record.values['_value'] / 300)
                except:
                    return 0
    
    # query = 'from(bucket: "trace") \
    #             |> range(start: {}, stop: {}) \
    #             |> filter(fn: (r) => r["_measurement"] == "service_metric" and r["_field"] == "latency") \
    #             |> group(columns: ["service"]) \
    #             |> toFloat() \
    #             |> quantile(q: {}, column:"_value") \
    #             '.format(start_time, end_time, "0.50")
    # tables = influxclient.query_api().query(query, org=org)
    # for table in tables:
    #     for record in table.records:
    #         service = record.values['service']
    #         data50[service] = record.values['_value']
# 
    # query = 'from(bucket: "trace") \
    #         |> range(start: {}, stop: {}) \
    #         |> filter(fn: (r) => r["_measurement"] == "service_metric" and r["_field"] == "latency" and r["service"] == "cartservice") \
    #         |> group(columns: ["op"]) \
    #         |> toFloat() \
    #         |> quantile(q: {}, column: "_value") \
    #         '.format(start_time, end_time,  "0.90")
    # # get p50, p75, p90, p99 latency of redisDB
    # tables = influxclient.query_api().query(query, org=org)
    # for table in tables:
    #     for record in table.records:
    #         service = record.values['op']
    #         data90[service] = record.values['_value']
    
    # query = 'from(bucket: "trace") \
    #         |> range(start: {}, stop: {}) \
    #         |> filter(fn: (r) => r["_measurement"] == "service_metric" and r["_field"] == "latency" and r["service"] == "cartservice") \
    #         |> group(columns: ["op"]) \
    #         |> toFloat() \
    #         |> quantile(q: {}, column: "_value") \
    #         '.format(start_time, end_time,  "0.50")
    # # get p50, p75, p90, p99 latency of redisDB
    # tables = influxclient.query_api().query(query, org=org)
    # for table in tables:
    #     for record in table.records:
    #         service = record.values['op']
    #         data50[service] = record.values['_value']

# start_time : approximately 10:10

# 14:10:30
end_time = datetime.datetime.now(datetime.timezone.utc)
# print(end_time)
end_time = end_time.replace(hour=10, minute=0, second=0, day=22)
start_time = end_time.replace(hour=0)
print(end_time, start_time)
# intervals = []
cnt = 0
data_list = []
data_50 = []
latency = []
while end_time >= start_time:
    end_ = end_time - datetime.timedelta(seconds=10)
    data = get(end_, end_time)
    if len(data) == 0:
        end_time = end_    
    else: # data exist in [end_, end_time], start query
        # cnt += 1
        # if cnt <= 20:
        #     continue
        # if cnt > 30:
        #     break
        end_ = end_time - datetime.timedelta(minutes=6)
        data90 = get(end_, end_time)
        data_list.append(data90)
        # latency.append(get_rps(end_, end_time))
        # data_50.append(data50)
        # intervals.append([end_, end_time])
        print(cnt, end_, end_time)
        end_time = end_

# print(data_list)
frontend=[]
for data_slice in data_list:
    frontend.append(data_slice["frontend"])
print(frontend)
print(latency)
np.save("frontend",frontend)
# print(data_list)
# np.save("res/p90data", data_list)
# np.save("res/p50data", data_50)
# print(intervals)