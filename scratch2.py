import sys
import os
import numpy as np
import csv
import pandas as pd
from scratch_const import *
import shutil
import re
import heapq
# def refresh_csv():
#     '''
#     add p95 into data*.csv
#     '''
#     for j in range(36):
#         filename = "res/newdata"+str(j)+".csv"
#         file = pd.read_csv(filename)
#         df = pd.DataFrame(file)
#         df.to_csv("res/data"+str(j)+".csv")

# def combine_parameters():
#     p1 = np.load("res0804/param300.npy", allow_pickle=True).item()
#     p2 = np.load("res/param300.npy", allow_pickle=True).item()
#     real_p = {}
#     for s in services:
#         real_p[s] = p1[s][:36] + p2[s][36:]
#     np.save("res/new_param300.npy", real_p)

# combine_parameters()

'''
merged+new -> clean -> remove outlier
'''



'''
combine results & parameter sets
'''
def merge_paras():
    # para1 = np.load("res_collection/res0813/param_50.npy", allow_pickle=True).item()
    # para2 = np.load("res_collection/res0814/param_100.npy", allow_pickle=True).item()
    # para3 = np.load("res_collection/res0816/param_500.npy", allow_pickle=True).item()
    para4 = np.load("res_collection/res0811/param_300.npy", allow_pickle=True).item()
    para5 = np.load("res_collection/res0812/param_300.npy", allow_pickle=True).item()
    para6 = np.load("res_collection/res0909/param_300.npy", allow_pickle=True).item()
    para = {}
    for s in services:
        para[s] = para4[s]+para5[s]+para6[s]
    np.save("res_merged_new/param.npy", para)

def move_csvs():
    # for i in range(50):
    #     shutil.copy("res_collection/res0813/data"+str(i)+".csv", "res_merged_new/data"+str(i)+".csv")
    # for i in range(100):
    #     shutil.copy("res_collection/res0814/data"+str(i)+".csv", "res_merged_new/data"+str(i+50)+".csv")
    # for i in range(500):
    #     shutil.copy("res_collection/res0816/data"+str(i)+".csv", "res_merged_new/data"+str(i+150)+".csv")
    for i in range(300):
        shutil.copy("res_collection/res0811/data"+str(i)+".csv", "res_merged_new/data"+str(i)+".csv")
    for i in range(300):
        shutil.copy("res_collection/res0812/data"+str(i)+".csv", "res_merged_new/data"+str(i+300)+".csv")
    for i in range(300):
        shutil.copy("res_collection/res0909/data"+str(i)+".csv", "res_merged_new/data"+str(i+600)+".csv")

def move_wrk_table():
    # for i in range(50):
    #     shutil.copy("wrk_collection/wrk_table0813/"+str(i), "wrk_rps_merged/"+str(i))
    # for i in range(100):
    #     shutil.copy("wrk_collection/wrk_table0814/"+str(i), "wrk_rps_merged/"+str(i+50))
    # for i in range(500):
    #     shutil.copy("wrk_collection/wrk_table0816/"+str(i), "wrk_rps_merged/"+str(i+150))
    for i in range(300):
        shutil.copy("wrk_collection/wrk_table0811/"+str(i), "wrk_rps_merged/"+str(i))
    for i in range(300):
        shutil.copy("wrk_collection/wrk_table0812/"+str(i), "wrk_rps_merged/"+str(i+300))
    for i in range(300):
        shutil.copy("wrk_collection/wrk_table0909/"+str(i), "wrk_rps_merged/"+str(i+600))


'''
check timeout & 500 errors
'''
def check_quality():
    # invalid_list = []
    cnt = 0
    para = {}
    latency = []
    para_ori = np.load("res_collection/res0909/param_300.npy", allow_pickle=True).item()
    for s in services:
        para[s] = []
    for i in range (300):
        with open("wrk_collection/wrk_table0909/"+str(i)) as f:
            text = f.read()
            timeout = re.search(r'.* timeout (\d*?)\s.*', str(text))
            response500 = re.search(r'.*Non-2xx or 3xx responses: (\d*?)\s.*', str(text))
            if response500:
                num = int(response500.group(1))
                if num > 300:
                    # invalid data
                    print(i, "response500", num)
                    # invalid_list.append(i)
                    continue
            
            if timeout:
                num = int(timeout.group(1))
                if num > 100:
                    print(i, "timeout", num)
                    continue

            if i == 605:
                continue # TODO: this one is not usable
            
            # merge data
            for s in services:
                para[s].append(para_ori[s][i])
            data = pd.read_csv("res_collection/res0909/data"+str(i)+".csv")
            
            for row in range(14):
                # data.loc[row]用来取出一个service对应的行
                r = data.loc[row]
                if r["service"] == "frontend":
                    latency.append(float(r["0.90"]))
                #     continue
                # for p in perf:
                #     csv_onedic[r["service"]+":"+p].append(float(r[p]))
            # shutil.copy("res_collection/res0909/data"+str(i)+".csv", "res1004/data"+str(cnt)+".csv")
            cnt += 1

    print(cnt)
    print(len(para["frontend"]))
    np.save("res1004/param.npy", para)
    return latency


# # from res_clean folder to res_rm_outlier folder
# def check_outlier(length):
#     p90 = []
#     for i in range(length):
#         data = pd.read_csv("res_clean_rps_scale/data"+str(i)+".csv")
#         for row in range(14):
#             # data.loc[row]用来取出一个service对应的行
#             r = data.loc[row]
#             if r["service"] == "frontend":
#                 p90.append(r["0.90"])
#                 # print(r["0.90"])
#     return p90

# def rm_outlier(length):
#     '''
#     get the positions of the data points to be removed
#     in this case, is [498, 198, 44, 210, 544, 599, 101, 257]
#     '''
#     p90 = check_outlier(length)
#     # print(p90)
#     sub = heapq.nlargest(int(length/100)+1, range(len(p90)), p90.__getitem__)
#     print(sub)
#     '''
#     delete such points
#     '''
#     cnt = 0
#     para = {}
#     para_ori = np.load("res_clean_rps_scale/param.npy", allow_pickle=True).item()
#     for s in services:
#         para[s] = []
#     for i in range (length):
#         if i in sub:
#             continue
#         else:
#             for s in services:
#                 para[s].append(para_ori[s][i])
#             shutil.copy("res_clean_rps_scale/data"+str(i)+".csv", "res_rm_outlier_scale/data"+str(cnt)+".csv")
#             cnt += 1
            
#     print(cnt)
#     print(len(para["frontend"]))
#     np.save("res_rm_outlier_scale/param.npy", para)


def run():
    # merge_paras()
    # move_csvs()
    # move_wrk_table()
    lat = check_quality()
    print(np.mean(lat), np.std(lat))
    # rm_outlier(length)

# run()

lat = [443275.98190316604, 483200.41197089944, 304460.3214285716, 385926.0110837439, 1097169.053564947, 396765.1437585734, 430238.61338475195, 257273.56172759482, 456231.33312693436, 585196.9387902395, 596355.198684626, 427453.486904762, 342793.4222329887, 369502.8529411764, 1098718.798016449, 340429.4644970415, 1007022.21875, 314793.4773773774, 515463.5999517725, 323018.2939532334, 392943.09147098515, 506955.6481558028, 611621.774315098, 271867.53126684634, 1002065.8873736064, 1101643.054081633, 398692.5434318555, 2002629.8924696355, 493166.89527272736, 502382.5039513678, 380644.4296675192, 343224.0888594165, 706577.9521367523, 506186.0938184754, 413329.57301616564, 1701122.0522267206, 433617.58870392403, 301310.92960761, 410773.1450653983, 397683.2298591306, 306217.1079667063, 298239.1445239643, 202758.61834319527, 307573.0140350877, 563229.6052318669, 325176.7049799568, 393092.9647816349, 288621.95098814234, 541754.620332937, 504331.1813644689, 269152.69000564655, 390654.278243919, 692295.3787784679, 329382.46877654205, 414301.38901098905, 324325.4906064209, 414199.4052568121, 487179.05458553805, 288832.67797202803, 1699975.4798536585, 385849.69208314904, 488293.8518375241, 201493.88608799048, 579936.8874329502, 2302559.699, 332386.501111111, 423885.89280096797, 290242.7557692307, 160396.41125541125, 382110.7159277504, 226880.82359058567, 487764.01422715216, 502175.29763473826, 178849.24327704814, 1890629.1840909093, 411156.0386444708, 1070406.1789473684, 593383.7257575757, 1502130.0390588238, 527802.6985221673, 277015.4122202057, 664964.1911243626, 766049.5851648336, 560481.3593151676, 1703488.2464735266, 605795.8297265159, 314350.91940789483, 382650.99337135936, 398936.69932590105, 483308.13858165266, 394360.85686585377, 446137.60089285724, 252262.52598978285, 337886.23435504467, 394854.4173755657, 340701.80636277306, 505160.5390958448, 803261.0687062484, 392282.894299517, 305041.0966683951, 422053.3117448795, 254512.2057653713, 301072.1666666667, 885285.5031501168, 389511.6248513673, 588667.0516052318, 2000287.7403952568, 324680.97167487675, 345758.76619291696, 197690.10657142857, 307963.7592579186, 1999699.2990476186, 1498155.8708333333, 631224.9771099748, 474289.55481569556, 216174.67563779088, 298516.74732461374, 576030.1496738117, 409328.62783699064, 798411.3627551021, 618151.8632580261, 796081.289035624, 255074.1216622458, 808943.1920332937, 329823.0010781671, 845942.6761861554, 899199.8584795322, 211878.47110582644, 513114.66891954024, 311751.2229177719, 400185.72531760443, 415416.45208085625, 643595.8691647509, 852876.431864839, 708188.7178359098, 1731115.336111111, 400721.31343012693, 409989.23686088, 309022.950059453, 318961.7942986426, 429731.10865717946, 310189.2550892857, 385772.10819754965, 904072.6310204082, 589913.6838624339, 318318.4495974235, 292153.2838461538, 490555.1911070782, 235794.4896134454, 693419.5952279202, 336211.0508917954, 802752.1647648903, 709610.4106508878, 277235.70558858506, 297121.55370625795, 307016.848003848, 390890.65552913194, 2001098.2645833332, 478769.3723432403, 778637.7110194904, 355294.2467228607, 566227.0130223519, 342169.7315101072, 1395627.8142857142, 245354.09621621613, 430174.45038458216, 399050.63569023577, 390404.55648038053, 679300.4306818182, 292010.6022592152, 315014.3418549347, 274689.56785714295, 420731.1712247325, 392519.51119845675, 354733.0030075189, 613195.1429292929, 283539.2019283122, 323787.4960601632, 344917.3555993433, 770511.8678765873, 508033.48896551726, 294925.60927467304, 578098.3119263677, 897673.8003889034, 486117.02678571426, 337124.90122240473, 776325.8280864197, 414372.3331417624, 599773.5249546279, 711548.5410058028, 316123.653076923, 406261.316765755, 517625.27315315325, 450684.7544699873, 594876.4667711599, 398325.35375494073, 301337.8979785969, 458629.47993730404, 589906.8640664961, 413776.4541771339, 507974.4931739319, 647985.3790860666, 289056.98387698055, 410429.2349583829, 712165.3086124401, 443274.73203377915, 308765.2102324778, 496470.9232026144, 509099.1563005622, 372098.0100611916, 309395.4245700459, 508727.43036902597, 509089.07253269915, 500285.69830322947, 1699334.4844993143, 501392.39243589743, 699773.4322660097, 410510.7350904392, 605324.6609177861, 1082650.830177405, 330155.56104252406, 1901798.5563460696, 398831.2935256064, 435451.05552818876, 207312.61517241382, 276035.1168243523, 395779.1739130436, 620114.921383648, 296906.4359966359, 400744.2686483886, 511519.3636850747, 251965.66666666666, 718153.5178359097, 1429827.8537142845, 485111.60713305906, 362735.29714625457, 702401.4341836734, 1700628.4110344828, 797506.2104161824, 914990.6077192982, 515121.03027823236, 458842.0520833333, 502646.605691057, 343648.83080296894, 901765.9756244218, 494053.02100269555, 620065.2574889481, 466252.9037744865, 1902994.3901276598, 514581.4, 911176.1904718692, 382943.76147443516]
print(np.mean(lat), np.std(lat))