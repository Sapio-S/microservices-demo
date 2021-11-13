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
check if data is full
run this script before running scratch.py
'''

def combine_csv(size, route, wrk_route, rps_limit):
    rps = []
    p90 = []
    csv_onedic = []
    less_than_150 = []
    invalid_wrk = []
    for i in range(size):
        try:

            data = pd.read_csv(route+"data"+str(i)+".csv")
            for row in range(14):
                # data.loc[row]用来取出一个service对应的行
                r = data.loc[row]
                if r["service"] == "redis" or r["service"] == "total":
                    continue
                if r["service"] == "frontend":
                    rps0 = float(r["rps"])
                    if rps0 < rps_limit:
                        less_than_150.append(i)

            with open(wrk_route+str(i)) as f:
                text = f.read()
                timeout = re.search(r'.* timeout (\d*?)\s.*', str(text))
                response500 = re.search(r'.*Non-2xx or 3xx responses: (\d*?)\s.*', str(text))
                if response500:
                    num = int(response500.group(1))
                    if num > 0:
                        invalid_wrk.append(i)
                    # invalid data
                        # print(i, "response500", num)
                    # invalid_list.append(i)
                        continue
            
                if timeout:
                    num = int(timeout.group(1))
                    if num > 0:
                        invalid_wrk.append(i)
                        # print(i, "timeout", num)
                        continue
        except:
            csv_onedic.append(i)
    print(len(less_than_150))
    print(less_than_150)
    print(len(invalid_wrk))
    print(len(list(set(less_than_150).intersection(set(invalid_wrk))))) # intersection

    invalid_trials = list(set(less_than_150).union(set(invalid_wrk)))
    for i in range(size):
        if i in invalid_trials:
            continue
        data = pd.read_csv(route+"data"+str(i)+".csv")
        for row in range(14):
            # data.loc[row]用来取出一个service对应的行
            r = data.loc[row]
            if r["service"] == "frontend":
                rps0 = float(r["rps"])
                if rps0 > rps_limit:
                    p90.append(float(r["0.90"]))
                    rps.append(float(r["rps"]))
    print(len(rps))
    print(np.min(rps),np.max(rps))
    print("min=",np.min(p90), "max=",np.max(p90),"std=",np.std(p90), "avg=",np.mean(p90))

combine_csv(300,"res/","wrk_table/", rps_limit=0)
combine_csv(300,"res_collection/res0909/","wrk_collection/wrk_table0909/", rps_limit=0)
