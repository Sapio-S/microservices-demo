### 说明
此文件夹下的程序需要在根目录下运行。
### alter_res.py
需要将日期设置为2021.8.4，对已经采集的数据，重新查询influxDB找出p95和p50。
### alter_csv.py
- 通过p50对比p95的正确性。
- 在data0-data35内引入p95的数据，存储为newdata0-newdata35。