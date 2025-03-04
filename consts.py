const_dic = {
    "adservice":{
        "MAX_ADS_TO_SERVE":{
            "MAX":5,
            "MIN":1,
        },
        "CPU_LIMIT":{ # 300, request 200
            "MAX":500,
            "MIN":250,
        },
        "MEMORY_LIMIT":{ # 300, request 180
            "MAX":500,
            "MIN":250,
        },
        "IPV4_RMEM":{
            "MAX":6291456,
            "MIN":4096,
        },
        "IPV4_WMEM":{
            "MAX":4194304,
            "MIN":4096,
        }
    },
    "cartservice":{
        "CPU_LIMIT":{ # 300, request 200
            "MAX":500,
            "MIN":250, 
        },
        "MEMORY_LIMIT":{ # 128, request 64
            "MAX":250,
            "MIN":100,
        },
        "IPV4_RMEM":{
            "MAX":6291456,
            "MIN":4096,
        },
        "IPV4_WMEM":{
            "MAX":4194304,
            "MIN":4096,
        },
        # note: 以下为redis的配置，由于redis在cartservice中初始化，因此将参数移动到了这里
        "hash_max_ziplist_entries":{
            "MAX":4096,
            "MIN":32,
        },
        "maxmemory_samples":{
            "MAX":10,
            "MIN":1,
        },
        "maxmemory":{
            "MAX":16,
            "MIN":0,
        },
    },
    "checkoutservice":{
        "CPU_LIMIT":{ # 200, request 100
            "MAX":400,
            "MIN":150,
        },
        "MEMORY_LIMIT":{ # 128, request 64
            "MAX":250,
            "MIN":100,
        },
        "IPV4_RMEM":{
            "MAX":6291456,
            "MIN":4096,
        },
        "IPV4_WMEM":{
            "MAX":4194304,
            "MIN":4096,
        }
    },
    "currencyservice":{
        "CPU_LIMIT":{ # 200, request 100
            "MAX":400,
            "MIN":150,
        },
        "MEMORY_LIMIT":{ # 128, request 64
            "MAX":250,
            "MIN":100,
        },
        "IPV4_RMEM":{
            "MAX":6291456,
            "MIN":4096,
        },
        "IPV4_WMEM":{
            "MAX":4194304,
            "MIN":4096,
        }
    },
    "emailservice":{
        "CPU_LIMIT":{ # 200, request 100
            "MAX":400,
            "MIN":150,
        },
        "MEMORY_LIMIT":{ # 128, request 64
            "MAX":250,
            "MIN":100,
        },
        "MAX_WORKERS":{
            "MAX":20,
            "MIN":5,
        },
        "IPV4_RMEM":{
            "MAX":6291456,
            "MIN":4096,
        },
        "IPV4_WMEM":{
            "MAX":4194304,
            "MIN":4096,
        }
    },
    "frontend":{
        "CPU_LIMIT":{ # 200, request 100
            "MAX":400,
            "MIN":150,
        },
        "MEMORY_LIMIT":{ # 128, request 64
            "MAX":250,
            "MIN":100,
        },
        "IPV4_RMEM":{
            "MAX":6291456,
            "MIN":4096,
        },
        "IPV4_WMEM":{
            "MAX":4194304,
            "MIN":4096,
        }
    },
    "paymentservice":{
        "CPU_LIMIT":{ # 200, request 100
            "MAX":400,
            "MIN":150,
        },
        "MEMORY_LIMIT":{ # 128, request 64
            "MAX":250,
            "MIN":100,
        },
        "IPV4_RMEM":{
            "MAX":6291456,
            "MIN":4096,
        },
        "IPV4_WMEM":{
            "MAX":4194304,
            "MIN":4096,
        }
    },
    "productcatalogservice":{
        "CPU_LIMIT":{ # 200, request 100
            "MAX":400,
            "MIN":150,
        },
        "MEMORY_LIMIT":{ # 128, request 64
            "MAX":250,
            "MIN":100,
        },
        "IPV4_RMEM":{
            "MAX":6291456,
            "MIN":4096,
        },
        "IPV4_WMEM":{
            "MAX":4194304,
            "MIN":4096,
        }
    },
    "recommendationservice":{
        "CPU_LIMIT":{ # 200, request 100
            "MAX":400,
            "MIN":150,
        },
        "MEMORY_LIMIT":{ # 450, request 220
            "MAX":800,
            "MIN":300,
        },
        "MAX_WORKERS":{
            "MAX":20,
            "MIN":5,
        },
        "MAX_RESPONSE":{
            "MAX":4,
            "MIN":1,
        },
        "IPV4_RMEM":{
            "MAX":6291456,
            "MIN":4096,
        },
        "IPV4_WMEM":{
            "MAX":4194304,
            "MIN":4096,
        }
    },
    "redis":{
        "CPU_LIMIT":{ # 125, request 70
            "MAX":350,
            "MIN":120,
        },
        "MEMORY_LIMIT":{ # 256, request 200
            "MAX":450,
            "MIN":250,
        },
        "IPV4_RMEM":{
            "MAX":6291456,
            "MIN":4096,
        },
        "IPV4_WMEM":{
            "MAX":4194304,
            "MIN":4096,
        },
    },
    "shippingservice":{
        "CPU_LIMIT":{ # 200, request 100
            "MAX":400,
            "MIN":150,
        },
        "MEMORY_LIMIT":{ # 128, request 64
            "MAX":250,
            "MIN":100,
        },
        "IPV4_RMEM":{
            "MAX":6291456,
            "MIN":4096,
        },
        "IPV4_WMEM":{
            "MAX":4194304,
            "MIN":4096,
        }
    },
}