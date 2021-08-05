import sys
import os
import numpy as np
import csv
import pandas as pd
def changecsv():
    pass

p50 = np.load("res/p50data.npy",allow_pickle=True)
p95 = np.load("res/p95data.npy", allow_pickle=True)
cnt = 0
file_list = os.listdir("res/")
for j in range(36):
    filename = "res/data"+str(j)+".csv"
    file = pd.read_csv(filename)
    df = pd.DataFrame(file)
    df["0.95"] = [0.0]*len(df)
    for i in range(len(df)):
        document = df[i:i+1]
        service = document['service'][i]

        # validate data
        p50_ = document['0.50'][i]
        if service == "redis" or service == "total":
            continue
        f1 = float(p50_)
        f2 = float(p50[35-j][service])
        try:
            diff = round((f1-f2)/(f2), 4)
        except:
            diff = round((f1-f2),4)
        if diff > 0.05:
            cnt += 1
            print("in data", j, service, "new",f1,"old", f2, diff)

        # add p95 data
        f3 = float(p95[35-j][service])
        document['0.95'][i] = f3
    df.to_csv("res/newdata"+str(j)+".csv")

        
print(cnt)

