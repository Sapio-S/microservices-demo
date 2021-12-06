import sys
import os
import numpy as np
import csv
import pandas as pd
import shutil
import re
import heapq

'''
check timeout & 500 errors
'''
def check_quality():
    rps = []
    p90 = []
    cnt = 0
    para = {}
    for i in range (13):
        latency_infite = False
        data = pd.read_csv("res/data"+str(i)+".csv")
        try:
            for row in range(14):
                r = data.loc[row]
                if r["service"] == "frontend":
                    rps.append(float(r["rps"]))
                    p90.append(float(r["0.90"]))
                #     if rps < 110 or rps > 170:
                #         print(i, "rps invalid")
                #         # rps_valid=False
                #         continue
        except:
            continue
        with open("wrk_table/"+str(i)) as f:
            text = f.read()
            timeout = re.search(r'.* timeout (\d*?)\s.*', str(text))
            response500 = re.search(r'.*Non-2xx or 3xx responses: (\d*?)\s.*', str(text))
            if response500:
                num = int(response500.group(1))
                if num > 300:
                    print(i, "response500", num)
                    cnt += 1
            # sentence = text.split("\n")
            # rrps = sentence[-3].split(" ")[-1]
            # rps.append(float(rrps))

    print(cnt)
    print("rps", np.mean(rps), np.std(rps))
    print("p90", np.mean(p90), np.std(p90))
    return cnt

def run():
    length = check_quality()

run()