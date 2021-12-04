# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

apiVersion: apps/v1
kind: Deployment
metadata:
  name: recommendationservice
spec:
  replicas: 2
  selector:
    matchLabels:
      app: recommendationservice
  template:
    metadata:
      labels:
        app: recommendationservice
    spec:
      securityContext:
        sysctls:
        - name: net.ipv4.tcp_rmem
          value: "4096        {{para.IPV4_RMEM}}  6291456"
        - name: net.ipv4.tcp_wmem
          value: "4096        {{para.IPV4_WMEM}}   4194304"
      serviceAccountName: default
      terminationGracePeriodSeconds: 5
      containers:
      - name: server
        image: recommendationservice
        ports:
        - containerPort: 8080
        readinessProbe:
          periodSeconds: 5
          exec:
            command: ["/bin/grpc_health_probe", "-addr=:8080"]
        livenessProbe:
          periodSeconds: 5
          exec:
            command: ["/bin/grpc_health_probe", "-addr=:8080"]
        env:
        - name: PORT
          value: "8080"
        - name: MAX_RESPONSE
          value: "{{para.MAX_RESPONSE}}"
        - name: MAX_WORKERS
          value: "{{para.MAX_WORKERS}}"
        - name: PRODUCT_CATALOG_SERVICE_ADDR
          value: "productcatalogservice:3550"
        resources:
          requests:
            cpu: 100m
            memory: 220Mi
          limits:
            cpu: {{para.CPU_LIMIT}}m
            memory: {{para.MEMORY_LIMIT}}Mi
---
apiVersion: v1
kind: Service
metadata:
  name: recommendationservice
spec:
  clusterIP: None
  selector:
    app: recommendationservice
  ports:
  - name: grpc
    port: 8080
    targetPort: 8080
