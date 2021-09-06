import numpy as np
import re
from consts import const_dic
import os,sys

# paras = np.load("/home/yuqingxie/microservices-demo/res/param_5.npy",allow_pickle=True).item()
# for i in range(5):
#     for k, item in paras.items():
#         print(k,item[i])
#     print(i)

'''
check the quality of collected data
'''
# para = np.load("res/param_10.npy", allow_pickle=True)
# print(para)
# limit_ok = {}
# for s in const_dic:
#     limit_ok[s] = {}
#     for p in const_dic[s]:
#         limit_ok[s][p] = False

limit = {}
working = {}
cnt = 0
for s in const_dic:
    limit[s] = []
    working[s] = []
total_date =  ["0811","0812", "0813", "0814", "0816","0822","0827","0831"]
not_working_settings = []
working_settings = []
size = {"0813":50, "0814":100, "0816":500,"0822":50,"0827":150,"0831":300}
for date in ["0813", "0814", "0816"]:
    param_setting = np.load("res_collection/res"+date+"/param_"+str(size[date])+".npy", allow_pickle = True).item()
    # wrk_settings = np.load("res_collection/res"+date+"/wrk_para.npy")
    for i in range (500):
        try:
            with open("wrk_collection/wrk_table"+date+"/"+str(i)) as f:
                text = f.read()
                timeout = re.search(r'.* timeout (\d*?)\s.*', str(text))
                response500 = re.search(r'.*Non-2xx or 3xx responses: (\d*?)\s.*', str(text))
                if timeout:
                    num = int(timeout.group(1))
                    if num > 100:
                        continue
                        print(date, i, "timeout", num)
                        not_working_settings.append(wrk_settings[i])
                else:
                    working_settings.append(wrk_settings[i])
                if response500:
                    num = int(response500.group(1))
                    if num > 30:
                        continue
                        if param_setting["shippingservice"][i]["IPV4_RMEM"] <= 14032:
                            continue
                        cnt += 1
                        # for f in const_dic:
                        #     limit[f].append(param_setting[f][i])
                        print(date, i, "response500",num)
                else:
                    for f in const_dic:
                        working[f].append(param_setting[f][i])
                cnt += 1
        except:
            continue
print(cnt)
# for f in const_dic:
#     for para in limit[f][0]:
#         tmp_list = []
#         for i in range(len(limit[f])):
#             tmp_list.append(limit[f][i][para])
#         print(f, para, np.min(tmp_list), np.max(tmp_list))

# for f in const_dic:
#     for para in working[f][0]:
#         tmp_list = []
#         for i in range(len(working[f])):
#             tmp_list.append(working[f][i][para])
#         print(f, para, np.min(tmp_list), np.max(tmp_list))

# for i in len(limit):
#     for f in const_dic:
#         for l in limit[f][i]:

# print("working parameters")
# # for i in not_working_settings:
# #     print(i)
# p56 = []
# for k in range(len(working_settings)):
#     tmp = 1-not_working_settings[k][0]-not_working_settings[k][1]-not_working_settings[k][2]-not_working_settings[k][3]
#     if tmp < 0.20:
#         print(k)
#         for i in range(5):
#             p = not_working_settings[k][i]
#             maxi = np.max(working_settings[:][i])
#             mini = np.min(working_settings[:][i])
#             if p < mini:
#                 print("parameter",i,"too small in ",k,"diff",mini-p)
#             if p > maxi:
#                 print("parameter",i,"too large in ",k,"diff",p-maxi)
        # print(not_working_settings[k])
#     p56.append(1-working_settings[k][0]-working_settings[k][1]-working_settings[k][2]-working_settings[k][3])
# print(np.max(p56))
# for i in range(5):
#     # print(i)
#     f = open("log"+str(i),"w")
#     sys.stdout = f
#     for k in range(len(working_settings)):
#         print(working_settings[k][i])
    # print(np.min(not_working_settings[:][i]),np.max(not_working_settings[:][i]))

# print("working parameters")
# for i in working_settings:
#     print(i)
# for i in range(5):
#     print(np.min(working_settings[:][i]),np.max(working_settings[:][i]))











# def generate_wrk():
#     former = np.random.random() / 20 * 3 + 0.8 # [0.8, 0.95]
#     add2cart_ratio = np.random.random() * (1 - former)

#     index_ratio = np.random.random() / 10 # [0, 0.1]
#     setCurrency_ratio = np.random.random() / 5 # [0, 0,2]
#     browseProduct_ratio = np.random.random() / 2 + 0.25 # [0.25, 0.75]
#     viewCart_ratio = np.random.random() / 3 # [0, 0.33]
#     s = index_ratio+setCurrency_ratio+browseProduct_ratio+viewCart_ratio
#     index_ratio = index_ratio * former / s
#     setCurrency_ratio = setCurrency_ratio* former / s
#     browseProduct_ratio = browseProduct_ratio* former / s
#     viewCart_ratio = viewCart_ratio* former / s

#     return index_ratio, setCurrency_ratio, browseProduct_ratio, viewCart_ratio, add2cart_ratio


# for i in range(10):
#     a,b,c,d,e = generate_wrk()
#     print(a+b+c+d,e,1-a-b-c-d-e)
#     # if a+b+c+d <= 0.8:
#     #     print(a,b,c,d,e)