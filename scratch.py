import sys
import os
import numpy as np
import csv
import pandas as pd
from scratch_const import *
import shutil
import re
import heapq

'''
check timeout & 500 errors
'''
def check_quality():
    # invalid_list = []
    cnt = 0
    para = {}
    para_ori = np.load("res/param_300.npy", allow_pickle=True).item()
    for s in services:
        para[s] = []
    for i in range (157):
        # check if we miss any data
        data = pd.read_csv("res/data"+str(i)+".csv")
        rps_valid = True
        try:
            for row in range(14):
                # data.loc[row]用来取出一个service对应的行
                r = data.loc[row]
                if r["service"] == "frontend":
                    rps=float(r["rps"])
                    if rps < 110 or rps > 170:
                        print(i, "rps invalid")
                        rps_valid=False
                        continue
        except:
            continue
        latency_infite = False
        with open("wrk_table/"+str(i)) as f:
            text = f.read()
            timeout = re.search(r'.* timeout (\d*?)\s.*', str(text))
            response500 = re.search(r'.*Non-2xx or 3xx responses: (\d*?)\s.*', str(text))
            if response500:
                num = int(response500.group(1))
                if num > 300:
                    # invalid data
                    print(i, "response500", num)
                    # invalid_list.append(i)
                    # continue
                    latency_infite = True
            
            if not rps_valid:
                continue
            
            for s in services:
                para[s].append(para_ori[s][i])

            # merge data
            if latency_infite:
                data = pd.read_csv("res/data"+str(i)+".csv")
                data['0.90'][5] = 10000000
                data.to_csv("res_tmp/data"+str(cnt)+".csv")
                # shutil.copy("res/data"+str(i)+".csv", "res_inf/data"+str(i)+".csv")
            else:
                shutil.copy("res/data"+str(i)+".csv", "res_tmp/data"+str(cnt)+".csv")
            cnt += 1

    print(cnt)
    print(len(para["frontend"]))
    np.save("res_tmp/param.npy", para)
    return cnt


# from res_clean folder to res_rm_outlier folder
def check_outlier(length):
    p90 = []
    for i in range(length):
        data = pd.read_csv("res_tmp/data"+str(i)+".csv")
        for row in range(14):
            # data.loc[row]用来取出一个service对应的行
            r = data.loc[row]
            if r["service"] == "frontend":
                p90.append(r["0.90"])
                # print(r["0.90"])
    return p90

# def rm_outlier(length):
#     '''
#     get the positions of the data points to be removed
#     in this case, is [498, 198, 44, 210, 544, 599, 101, 257]
#     '''
#     p90 = check_outlier(length)
#     # print(p90)
#     sub = heapq.nlargest(int(length/100)+1, range(len(p90)), p90.__getitem__)
#     print(sub)
#     '''
#     delete such points
#     '''
#     cnt = 0
#     para = {}
#     para_ori = np.load("res_tmp/param.npy", allow_pickle=True).item()
#     for s in services:
#         para[s] = []
#     for i in range (length):
#         if i in sub:
#             continue
#         else:
#             for s in services:
#                 para[s].append(para_ori[s][i])
#             shutil.copy("res_tmp/data"+str(i)+".csv", "res_tmp_final/data"+str(cnt)+".csv")
#             cnt += 1
            
#     print(cnt)
#     print(len(para["frontend"]))
#     np.save("res_tmp_final/param.npy", para)


def run():
    length = check_quality()
    # rm_outlier(length)

run()