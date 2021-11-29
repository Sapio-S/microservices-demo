import csv
import re
import numpy as np
# print("pred")
# for train_size in [10,25,50,100,150,200,300,400]:
#     print(train_size)
#     for i in range(10):
#         with open('test_checkout_150/GP_single_'+str(train_size)+"_"+str(i)) as f:
#             text = f.read()
#             sentence = text.split()
#             print(sentence[-1])
#     print()

print("real")
for train_size in [10,25,50,100]:
    response = []
    print(train_size)
    for i in range(10):
        with open('test_res/GP_single_'+str(train_size)+"_"+str(i)) as f:
            text = f.read()
            timeout = re.search(r'.* timeout (\d*?)\s.*', str(text))
            response500 = re.search(r'.*Non-2xx or 3xx responses: (\d*?)\s.*', str(text))
            
            if response500:
                num = int(response500.group(1))
                if num > 300:
                    # invalid data
                    response.append(num)
                    # print(i, "response500", num)
                    # invalid_list.append(i)
                    # continue
            
            # if timeout:
            #     num = int(timeout.group(1))
            #     if num > 100:
            #         # print(i, "timeout", num)
            #         continue

        with open('test_res/dataGP_single_'+str(train_size)+"_"+str(i)+".csv") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row["service"] == "frontend":
                    print(row["0.90"])
        
    print()
    print(len(response))
    print()

# print("MAE")
# for train_size in [10,25,50,100]:
#     print(train_size)
#     for i in range(10):
#         with open('test_checkout_150/GP_single_'+str(train_size)+"_"+str(i)) as f:
#             text = f.read()
#             MAE = re.search(r'test MAE is (\d+(\.\d+)?)[.\n]*', str(text))
#             if MAE:
#                 print(MAE.group(1))
#                 # mae = float(MAE.group(1))
#                 # print(mae)
#     print()
