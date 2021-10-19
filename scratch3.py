import sys
import os
import numpy as np
import csv
import pandas as pd
from scratch_const import *
import shutil
import re
import heapq
import jinja2
import subprocess
import time
import random
import yaml
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
'''
see which parameter setting causes problems. 
'''

# def check_quality():
#     invalid_list = []
#     cnt = 0
#     para = {}
#     para_ori = np.load("res_collection/res0909/param_300.npy", allow_pickle=True).item()
#     wrkload = np.load("res_collection/res0909/wrk_para.npy", allow_pickle=True)
#     for s in services:
#         para[s] = []
#     for i in range (300):
#         with open("wrk_collection/wrk_table0909/"+str(i)) as f:
#             text = f.read()
#             timeout = re.search(r'.* timeout (\d*?)\s.*', str(text))
#             response500 = re.search(r'.*Non-2xx or 3xx responses: (\d*?)\s.*', str(text))
#             if response500:
#                 num = int(response500.group(1))
#                 if num > 10000:
#                     # invalid data
#                     print(i, "response500", num)
#                     invalid_list.append(i)
#                     # print(para_ori[i])
#                     break
#                     continue
            
#             if timeout:
#                 num = int(timeout.group(1))
#                 if num > 100:
#                     print(i, "timeout", num)
#                     continue

#     for s in services:
#         para[s] = []
#     for s in services:
#         para[s].append(para_ori[s][i])
#     print(para)
#     print(wrkload[i])

# check_quality()


'''
use the failed parameter setting to see which pod restarts the most
'''
def generate_yaml(epoch):
    '''
    填充参数，生成对应的yaml文件
    '''
    para_dic={'adservice': [{'MAX_ADS_TO_SERVE': 2, 'CPU_LIMIT': 433, 'MEMORY_LIMIT': 234, 'IPV4_RMEM': 3095673, 'IPV4_WMEM': 3234553}], 'cartservice': [{'CPU_LIMIT': 225, 'MEMORY_LIMIT': 145, 'IPV4_RMEM': 5355315, 'IPV4_WMEM': 807719, 'hash_max_ziplist_entries': 3652, 'maxmemory_samples': 9, 'maxmemory': 80}], 'checkoutservice': [{'CPU_LIMIT': 596, 'MEMORY_LIMIT': 222, 'IPV4_RMEM': 4708647, 'IPV4_WMEM': 543818}], 'currencyservice': [{'CPU_LIMIT': 165, 'MEMORY_LIMIT': 150, 'IPV4_RMEM': 4705528, 'IPV4_WMEM': 3263839}], 'emailservice': [{'CPU_LIMIT': 292, 'MEMORY_LIMIT': 239, 'MAX_WORKERS': 17, 'IPV4_RMEM': 5468288, 'IPV4_WMEM': 4140648}], 'frontend': [{'CPU_LIMIT': 551, 'MEMORY_LIMIT': 196, 'IPV4_RMEM': 4309664, 'IPV4_WMEM': 1642585}], 'paymentservice': [{'CPU_LIMIT': 322, 'MEMORY_LIMIT': 93, 'IPV4_RMEM': 815511, 'IPV4_WMEM': 497696}], 'productcatalogservice': [{'CPU_LIMIT': 226, 'MEMORY_LIMIT': 173, 'IPV4_RMEM': 1369584, 'IPV4_WMEM': 2638980}], 'recommendationservice': [{'CPU_LIMIT': 154, 'MEMORY_LIMIT': 471, 'MAX_WORKERS': 20, 'MAX_RESPONSE': 1, 'IPV4_RMEM': 5241000, 'IPV4_WMEM': 3601710}], 'shippingservice': [{'CPU_LIMIT': 284, 'MEMORY_LIMIT': 84, 'IPV4_RMEM': 3882502, 'IPV4_WMEM': 821543}], 'redis': [{'CPU_LIMIT': 73, 'MEMORY_LIMIT': 267, 'IPV4_RMEM': 1020046, 'IPV4_WMEM': 723188}]}
    for service in services:
        para=para_dic[service][epoch]
        env = jinja2.Environment(loader=jinja2.FileSystemLoader("kubernetes-manifests-tpl"))
        temp = env.get_template(service+".yaml.tpl")
        temp_out = temp.render(para=para)
        with open(os.path.join("generated-manifests", service+'.yaml'), 'w') as f:
            f.writelines(temp_out)
            f.close()
    
generate_yaml(0)

def generate_wrk():
    env = jinja2.Environment(loader=jinja2.FileSystemLoader("wrk"))
    temp = env.get_template("script.lua.tpl")
    temp_out = temp.render(
        index_ratio=0.05816469,
        setCurrency_ratio=0.0661721,
        browseProduct_ratio=0.54236449,
        viewCart_ratio=0.28135689,
        add2cart_ratio=0.04770507,
        )
    with open("wrk/generated-script.lua", 'w') as f:
        f.writelines(temp_out)
        f.close()
generate_wrk()