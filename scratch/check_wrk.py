import numpy as np
import re
from consts import const_dic
import os

# paras = np.load("/home/yuqingxie/microservices-demo/res/param_5.npy",allow_pickle=True).item()
# for i in range(5):
#     for k, item in paras.items():
#         print(k,item[i])
#     print(i)

'''
check the quality of collected data
'''
para = np.load("res0811/param_300.npy", allow_pickle=True).item()
limit_ok = {}
for s in const_dic:
    limit_ok[s] = {}
    for p in const_dic[s]:
        limit_ok[s][p] = False

for i in range (300):
    with open("/home/yuqingxie/microservices-demo/wrk_table0811/"+str(i)) as f:
        text = f.read()
        timeout = re.search(r'.* (timeout \d*?)\s.*', str(text))
        response500 = re.search(r'.*Non-2xx or 3xx responses: (\d*?)\s.*', str(text))
        if response500:
            num = int(response500.group(1))
            if num > 1000:
                print(i, num)
                # for s in para: 
                    # print(para[s][i])
                    # for p in para[s][i]:
                    #     val = para[s][i][p]
                    #     min_val = const_dic[s][p]["MIN"]
                    #     if val/min_val < 1.05:
                    #         print(s, p, val, min_val)
        else:
            for s in para: 
                for p in para[s][i]:
                    val = para[s][i][p]
                    min_val = const_dic[s][p]["MIN"]
                    max_val = const_dic[s][p]["MAX"]
                    if (val-min_val)/(max_val-min_val) <= 1/300:
                        limit_ok[s][p] = True
                        # print(s, p, val, min_val)

for s in limit_ok:
    for p in limit_ok[s]:
        if limit_ok[s][p]:
            continue
        else:
            print(s, p)                        
        # print(i(, timeout.group(1) if timeout else "",response500.group(1) if response500 else "")

'''
check start & end times are collected
'''
# start = np.load("res/start.npy", allow_pickle = True)
# print(start)