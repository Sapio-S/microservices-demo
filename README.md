# 运行方式

### preparation
mkdir generated-manifests, res, wrk_table, locust_table

使用minikube启动：
minikube start --cpus=4 --memory 4096 --disk-size 32g --extra-config="kubelet.allowed-unsafe-sysctls=net.ipv4.*"

`python3 run.py`

/home/yuqingxie/wrk2/wrk -t10 -L -c100 -d5m --timeout 5s -s /home/yuqingxie/microservices-demo/wrk/script.lua -R100 http://10.96.142.239:80 --timeout 5s

/home/yuqingxie/wrk2/wrk -t10 -L -c100 -d5m --timeout 5s -s /home/yuqingxie/microservices-demo/wrk/generated-script.lua -R100 http://10.109.216.96 --timeout 10s

kubectl get svc frontend
/home/yuqingxie/wrk2/wrk -t5 -L -c50 -d5m --timeout 10s -s /home/yuqingxie/microservices-demo/wrk/script.lua -R150 http://10.110.154.30

/home/yuqingxie/.local/bin/locust -u 500 -r 50 -f src/loadgenerator/locustfile_original.py --headless --run-time 5m --host http://10.110.77.252:80 --csv=locust_table/test

full set:
skaffold run --default-repo=sapios
kubectl get svc frontend
/home/yuqingxie/wrk2/wrk -t10 -L -c100 -d5m --timeout 5s -s /home/yuqingxie/microservices-demo/wrk/generated-script.lua -R100 http://10.97.141.102 --timeout 10s
skaffold delete