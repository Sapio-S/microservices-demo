import csv
import re

# print("pred")
# for train_size in [10,25,50,100]:
#     print(train_size)
#     for i in range(10):
#         with open('test_checkout_150/GP_2checkout_'+str(train_size)+"_"+str(i)) as f:
#             text = f.read()
#             sentence = text.split()
#             print(sentence[-1])
#     print()

# print("real")
# for train_size in [10,25,50,100]:
#     print(train_size)
#     for i in range(10):
#         with open('test_res/dataGP_2checkout_'+str(train_size)+"_"+str(i)+".csv") as csvfile:
#             reader = csv.DictReader(csvfile)
#             for row in reader:
#                 if row["service"] == "frontend":
#                     print(row["0.90"])
#     print()

print("MAE")
for train_size in [10,25,50,100]:
    print(train_size)
    for i in range(10):
        with open('test_checkout_150/fluxion_2checkout_'+str(train_size)+"_"+str(i)) as f:
            text = f.read()
            MAE = re.search(r'test MAE is (\d+(\.\d+)?)[.\n]*', str(text))
            if MAE:
                print(MAE.group(1))
                # mae = float(MAE.group(1))
                # print(mae)
    print()
