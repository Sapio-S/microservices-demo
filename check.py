import csv
import sys
import numpy as np
csv_route = "locust_table/"

rate = []
for i in range(119):
    with open(csv_route+str(i)+'_stats.csv', 'r+') as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader]
        last_row = rows[-1]
        rate.append(int(last_row["Failure Count"])/int(last_row["Request Count"]))

para = np.load("res/param300.npy", allow_pickle=True).item()
# print(para)
services = ["adservice", "cartservice", "checkoutservice", "currencyservice", "emailservice", "frontend", "paymentservice", "productcatalogservice", "recommendationservice", "redis", "shippingservice"]

for i in range(120):
    print("\n_________________________begin ", i, "_____________________________")
    for s in services:
        print(para[s][i])
    print(rate[i])
