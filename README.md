# 运行方式

### preparation
mkdir generated-manifests, res, wrk_table, locust_table

使用minikube启动：
minikube start --cpus=4 --memory 4096 --disk-size 32g --extra-config="kubelet.allowed-unsafe-sysctls=net.ipv4.*"

`python3 run.py`