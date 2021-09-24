import os, sys
import numpy as np
import re
import pandas as pd
workable = []
for i in range (350):
    with open("wrk_table/"+str(i)) as f:
        text = f.read()
        timeout = re.search(r'.* timeout (\d*?)\s.*', str(text))
        response500 = re.search(r'.*Non-2xx or 3xx responses: (\d*?)\s.*', str(text))
        if timeout:
            num = int(timeout.group(1))
            if num > 100:
                continue
        if response500:
            num = int(response500.group(1))
            if num > 30:
                continue
        workable.append(i)

latency = []
for i in workable:
    data = pd.read_csv("res/data"+str(i)+".csv")
    for row in range(14):
        # data.loc[row]用来取出一个service对应的行
        r = data.loc[row]
        if r["service"] == "frontend":
            latency.append(float(r["0.90"]))

print(latency)
print("num: ", len(latency))
print("mean: ",np.mean(latency))
print("std: ", np.std(latency))