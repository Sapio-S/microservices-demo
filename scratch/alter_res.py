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
token = "pNFkiKKMTEVV9fYn-vk21om5hGpbH1lwbnuCsengK0RagjE48468gcSerxQILPZcVTRrrGK4iJMtPRsW87kvqA=="
org = "msra"
bucket = "trace"

influxclient = InfluxDBClient(url="http://localhost:8086", token=token)
quantile = ["0.50", '0.95']
# start_time = datetime.now(timezone.utc).astimezone().isoformat()
# end_time = datetime.now(timezone.utc).astimezone().isoformat()
def get(start_time, end_time):
    start_time = start_time.astimezone().isoformat()
    end_time = end_time.astimezone().isoformat()
    data95 = {}
    data50 = {}
    flag = False
    query = 'from(bucket: "trace") \
                |> range(start: {}, stop: {}) \
                |> filter(fn: (r) => r["_measurement"] == "service_metric" and r["_field"] == "latency") \
                |> group(columns: ["service"]) \
                |> toFloat() \
                |> quantile(q: {}, column:"_value") \
                '.format(start_time, end_time, "0.95")
    tables = influxclient.query_api().query(query, org=org)
    for table in tables:
        for record in table.records:
            flag = True
            service = record.values['service']
            data95[service] = record.values['_value']
    
    if not flag:
        return {}, {}

    query = 'from(bucket: "trace") \
                |> range(start: {}, stop: {}) \
                |> filter(fn: (r) => r["_measurement"] == "service_metric" and r["_field"] == "latency") \
                |> group(columns: ["service"]) \
                |> toFloat() \
                |> quantile(q: {}, column:"_value") \
                '.format(start_time, end_time, "0.50")
    tables = influxclient.query_api().query(query, org=org)
    for table in tables:
        for record in table.records:
            service = record.values['service']
            data50[service] = record.values['_value']

    query = 'from(bucket: "trace") \
            |> range(start: {}, stop: {}) \
            |> filter(fn: (r) => r["_measurement"] == "service_metric" and r["_field"] == "latency" and r["service"] == "cartservice") \
            |> group(columns: ["op"]) \
            |> toFloat() \
            |> quantile(q: {}, column: "_value") \
            '.format(start_time, end_time,  "0.95")
    # get p50, p75, p90, p99 latency of redisDB
    tables = influxclient.query_api().query(query, org=org)
    for table in tables:
        for record in table.records:
            service = record.values['op']
            data95[service] = record.values['_value']
    
    query = 'from(bucket: "trace") \
            |> range(start: {}, stop: {}) \
            |> filter(fn: (r) => r["_measurement"] == "service_metric" and r["_field"] == "latency" and r["service"] == "cartservice") \
            |> group(columns: ["op"]) \
            |> toFloat() \
            |> quantile(q: {}, column: "_value") \
            '.format(start_time, end_time,  "0.50")
    # get p50, p75, p90, p99 latency of redisDB
    tables = influxclient.query_api().query(query, org=org)
    for table in tables:
        for record in table.records:
            service = record.values['op']
            data50[service] = record.values['_value']
    return data95, data50

# start_time : approximately 10:10

# 14:10:30
end_time = datetime.datetime.now(datetime.timezone.utc)
end_time = end_time.replace(hour=6, minute=10, second=30, day=4)
start_time = end_time.replace(hour=0)
print(end_time, start_time)
# intervals = []
cnt = 0
data_list = []
data_50 = []
while end_time >= start_time:
    end_ = end_time - datetime.timedelta(seconds=10)
    data, _ = get(end_, end_time)
    if len(data) == 0:
        end_time = end_    
    else: # data exist in [end_, end_time], start query
        cnt += 1
        if cnt > 37:
            break
        end_ = end_time - datetime.timedelta(minutes=6)
        data95, data50 = get(end_, end_time)
        data_list.append(data95)
        data_50.append(data50)
        # intervals.append([end_, end_time])
        print(cnt, end_, end_time)
        end_time = end_

# print(data_list)
np.save("res/p95data", data_list)
np.save("res/p50data", data_50)
# print(intervals)