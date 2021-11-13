import csv
import numpy as np

def normalize(csv, k):
    dic = {}
    mini = np.min(csv)
    maxi = np.max(csv)
    dic[k+":MAX"] = maxi
    dic[k+":MIN"] = mini
    if maxi == mini:
        csv = [0.5 for i in range(len(csv))]
    else:
        csv = [(csv[i] - mini) / (maxi - mini) for i in range(len(csv))]
    return csv, dic

def standardize(csv, k):
    # compute scalers
    # dic = {}
    # std = np.std(csv)
    # avg = np.mean(csv)
    # dic[k+":STD"] = std
    # dic[k+":AVG"] = avg

    # load scalers
    dic = np.load("std_scaler_dataset_whole.npy", allow_pickle = True).item()
    # if k[:19] == "recommendation_pod0" or k[:19] == "recommendation_pod1":
    #     k = "recommendationservice"+k[19:]
    if k[:13] == "checkout_pod0" or k[:13] == "checkout_pod1":
        k = "checkoutservice"+k[13:]
    std = dic[k+":STD"]
    avg = dic[k+":AVG"]
    if std == 0:
        std = 1
    csv = [(csv[i] - avg) / std for i in range(len(csv))]
    return csv, dic

data = {}
para_dic = {}
with open("dataset-2checkout-150.csv") as csvfile:
    reader = csv.DictReader(csvfile)
    
    for name in reader.fieldnames:
        data[name] = []
    for row in reader:
        for name in reader.fieldnames:
            data[name].append(float(row[name]))
    for name in reader.fieldnames:
        data[name], scale = standardize(data[name], name)
        para_dic.update(scale)
        
    
    np.save("std_scaler_dataset_scale", para_dic)

    with open("dataset-2checkout-150-standardized.csv", "w") as f:
        writer = csv.DictWriter(f, reader.fieldnames)
        writer.writeheader()
        for i in range(528):
            writer.writerow({name:float(data[name][i]) for name in reader.fieldnames})
    
