import numpy as np
import os

route = "res_rm_outlier_rps/"
services = ["adservice", "cartservice", "checkoutservice", "currencyservice", "emailservice", "frontend", "paymentservice", "productcatalogservice", "recommendationservice", "shippingservice", "redis"]
quantile = ["0.50", '0.90', '0.95', '0.99']
headers = ["service", "rps","avg", "0.50", '0.90', '0.95', '0.99']
perf = ["rps", "avg", "0.50", '0.90', '0.95', '0.99']

# record service dependencies
extra_names = {
    "adservice":[],
    "cartservice":["get", "set"], 
    "checkoutservice":["paymentservice"],
    "checkoutservice":[],
    # "checkoutservice":["emailservice", "paymentservice", "shippingservice", "currencyservice", "productcatalogservice", "cartservice"], 
    "currencyservice":[], 
    "emailservice":[], 
    "frontend":["checkoutservice"],
    # "frontend":["adservice", "checkoutservice", "shippingservice", "currencyservice", "productcatalogservice", "recommendationservice", "cartservice"], 
    "paymentservice":[], 
    "productcatalogservice":[], 
    "recommendationservice":["productcatalogservice"], 
    "shippingservice":[], 
    "get":[], 
    "set":[]
}

finals = ["adservice", "cartservice", "checkoutservice", "currencyservice", "emailservice", "frontend", "paymentservice", "productcatalogservice", "recommendationservice", "shippingservice", "get", "set"]
collect = "frontend"

eval_metric_map = {
    '1':["0.90"],
    '2':["0.90", "0.50"],
    '3':["0.90", "0.50", "0.95"],
    '4':["0.90", "0.50", "0.95", "0.99"]
    }

# metrics = os.getenv("METRIC_NUM")
metrics = "1"
eval_metric = eval_metric_map[metrics]
# eval_metric = ["0.90", "0.50", "0.95", "0.99"]

scale_para = {
    "adservice":1000, 
    "cartservice":1000, 
    "checkoutservice":1000000, 
    "currencyservice":1000, 
    "emailservice":1000, 
    "frontend":1000000, 
    "paymentservice":1000, 
    "productcatalogservice":1000, 
    "recommendationservice":10000, 
    "shippingservice":1000, 
    "get":1000, 
    "set":1000,
    }
