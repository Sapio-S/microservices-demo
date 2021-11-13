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

token = "vcE9CCcTfVMFlYP6EQecuWys2VKfq_v59_FzR8YPNW0ScWUomNLlcB0_gzBIcZAfM0mBSFyj9Qf1kIofdxi-gQ=="
org = "msra"
bucket = "trace"
influxclient = InfluxDBClient(url="http://10.0.0.29:8086", token=token)

quantile = ["0.50", '0.90', '0.95', '0.99']

headers = ["service", "rps","avg", "0.50", '0.90', '0.95', '0.99']

# global variables
para_dic = {} # 参数配置，以service为基本单元


def query_db(duration=300):
    data = {}
    # generate service & DB keys 
    
    pod_name = {}
    cnt = 0
    # get rps of checkout pods
    for q in quantile:
        query = 'from(bucket: "trace") \
            |> range(start: -25m) \
            |> filter(fn: (r) => r["_measurement"] == "service_metric" and r["_field"] == "latency" and r["service"] == "checkoutservice") \
            |> group(columns: ["podname"]) \
            |> count() \
            '
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
            |> range(start: -25m) \
            |> filter(fn: (r) => r["_measurement"] == "service_metric" and r["_field"] == "latency" and r["service"] == "checkoutservice") \
            |> group(columns: ["podname"]) \
            |> toFloat() \
            |> quantile(q: {}, column: "_value") \
            '.format(q)
        tables = influxclient.query_api().query(query, org=org)
        for table in tables:
            for record in table.records:
                service = record.values['podname']
                if service is None:
                    continue
                data["checkout_pod"+str(pod_name[service])][q] = record.values['_value']
    print(data)
    print(pod_name)
    return data

def main():
    query_db()
main()