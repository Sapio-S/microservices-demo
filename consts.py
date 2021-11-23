consts = {
    "adservice":{
        "MAX_ADS_TO_SERVE":{
            "MAX":5,
            "MIN":1,
        },
        "CPU_LIMIT":{ # 300, request 200
            "MAX":500,
            "MIN":200,
        },
        "MEMORY_LIMIT":{ # 300, request 180
            "MAX":500,
            "MIN":180,
        },
        "IPV4_RMEM":{
            "MAX":6291456,
            "MIN":15000,
        },
        "IPV4_WMEM":{
            "MAX":4194304,
            "MIN":98000,
        }
    },
    "cartservice":{
        "CPU_LIMIT":{ # 300, request 200
            "MAX":500,
            "MIN":200, 
        },
        "MEMORY_LIMIT":{ # 128, request 64
            "MAX":250,
            "MIN":64,
        },
        "IPV4_RMEM":{
            "MAX":6291456,
            "MIN":39000,
        },
        "IPV4_WMEM":{
            "MAX":4194304,
            "MIN":64000,
        },
        # note: 以下为redis的配置，由于redis在cartservice中初始化，因此将参数移动到了这里
        "hash_max_ziplist_entries":{
            "MAX":4096,
            "MIN":64,
        },
        "maxmemory_samples":{
            "MAX":10,
            "MIN":1,
        },
        "maxmemory":{
            "MAX":200,
            "MIN":10,
        },
    },
    "checkoutservice":{
        "CPU_LIMIT":{ # 200, request 100
            "MAX":600,
            "MIN":130,
        },
        "MEMORY_LIMIT":{ # 128, request 64
            "MAX":250,
            "MIN":64,
        },
        "IPV4_RMEM":{
            "MAX":6291456,
            "MIN":38450,
        },
        "IPV4_WMEM":{
            "MAX":4194304,
            "MIN":59722,
        }
    },
    "currencyservice":{
        "CPU_LIMIT":{ # 200, request 100
            "MAX":400,
            "MIN":100,
        },
        "MEMORY_LIMIT":{ # 128, request 64
            "MAX":250,
            "MIN":64,
        },
        "IPV4_RMEM":{
            "MAX":6291456,
            "MIN":142068,
        },
        "IPV4_WMEM":{
            "MAX":4194304,
            "MIN":19690,
        }
    },
    "emailservice":{
        "CPU_LIMIT":{ # 200, request 100
            "MAX":400,
            "MIN":100,
        },
        "MEMORY_LIMIT":{ # 128, request 64
            "MAX":250,
            "MIN":64,
        },
        "MAX_WORKERS":{
            "MAX":20,
            "MIN":5,
        },
        "IPV4_RMEM":{
            "MAX":6291456,
            "MIN":35000,
        },
        "IPV4_WMEM":{
            "MAX":4194304,
            "MIN":50000,
        }
    },
    "frontend":{
        "CPU_LIMIT":{ # 200, request 100
            "MAX":600,
            "MIN":100,
        },
        "MEMORY_LIMIT":{ # 128, request 64
            "MAX":250,
            "MIN":64,
        },
        "IPV4_RMEM":{
            "MAX":6291456,
            "MIN":5000,
        },
        "IPV4_WMEM":{
            "MAX":4194304,
            "MIN":15000,
        }
    },
    "paymentservice":{
        "CPU_LIMIT":{ # 200, request 100
            "MAX":400,
            "MIN":100,
        },
        "MEMORY_LIMIT":{ # 128, request 64
            "MAX":250,
            "MIN":64,
        },
        "IPV4_RMEM":{
            "MAX":6291456,
            "MIN":115000,
        },
        "IPV4_WMEM":{
            "MAX":4194304,
            "MIN":29000,
        }
    },
    "productcatalogservice":{
        "CPU_LIMIT":{ # 200, request 100
            "MAX":400,
            "MIN":100,
        },
        "MEMORY_LIMIT":{ # 128, request 64
            "MAX":250,
            "MIN":64,
        },
        "IPV4_RMEM":{
            "MAX":6291456,
            "MIN":150000,
        },
        "IPV4_WMEM":{
            "MAX":4194304,
            "MIN":18000,
        }
    },
    "recommendationservice":{
        "CPU_LIMIT":{ # 200, request 100
            "MAX":600,
            "MIN":175,
        },
        "MEMORY_LIMIT":{ # 450, request 220
            "MAX":800,
            "MIN":250,
        },
        "MAX_WORKERS":{
            "MAX":30,
            "MIN":5,
        },
        "MAX_RESPONSE":{
            "MAX":4,
            "MIN":1,
        },
        "IPV4_RMEM":{
            "MAX":6291456,
            "MIN":20000,
        },
        "IPV4_WMEM":{
            "MAX":4194304,
            "MIN":40000,
        }
    },
    "redis":{
        "CPU_LIMIT":{ # 125, request 70
            "MAX":350,
            "MIN":70,
        },
        "MEMORY_LIMIT":{ # 256, request 200
            "MAX":450,
            "MIN":200,
        },
        "IPV4_RMEM":{
            "MAX":6291456,
            "MIN":30000,
        },
        "IPV4_WMEM":{
            "MAX":4194304,
            "MIN":22000,
        },
    },
    "shippingservice":{
        "CPU_LIMIT":{ # 200, request 100
            "MAX":400,
            "MIN":100,
        },
        "MEMORY_LIMIT":{ # 128, request 64
            "MAX":250,
            "MIN":64,
        },
        "IPV4_RMEM":{
            "MAX":6291456,
            "MIN":115000,
        },
        "IPV4_WMEM":{
            "MAX":4194304,
            "MIN":80000,
        }
    },
}