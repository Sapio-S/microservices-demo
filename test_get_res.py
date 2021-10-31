import csv
import re

# print("pred")
# for train_size in [10,25,50,100,150,200,300,400]:
#     print(train_size)
#     for i in range(5):
#         with open('test_2scale/DNN_2scale_'+str(train_size)+"_"+str(i)) as f:
#             text = f.read()
#             sentence = text.split()
#             print(sentence[-1])
#     print()

print("real")
for train_size in [10,25,50,100,150,200,300,400]:
    print(train_size)
    for i in range(5):
        with open('test_res/dataDNN_2scale_'+str(train_size)+"_"+str(i)+".csv") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row["service"] == "frontend":
                    print(row["0.90"])
    print()