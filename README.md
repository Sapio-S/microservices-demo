# 运行方式
启动时
minikube start --cpus=4 --memory 4096 --disk-size 32g --extra-config="kubelet.allowed-unsafe-sysctls=net.ipv4.*"
skaffold run
`python3 run.py`