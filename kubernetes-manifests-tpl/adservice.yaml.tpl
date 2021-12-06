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
  name: adservice
spec:
  replicas: 1
  selector:
    matchLabels:
      app: adservice
  template:
    metadata:
      labels:
        app: adservice
    spec:
      serviceAccountName: default
      terminationGracePeriodSeconds: 5
      securityContext:
        sysctls:
        - name: net.ipv4.tcp_rmem
          value: "4096        {{para.IPV4_RMEM}}  6291456"
        - name: net.ipv4.tcp_wmem
          value: "4096        {{para.IPV4_WMEM}}   4194304"
      containers:
      - name: server
        image: adservice
        ports:
        - containerPort: 9555
        env:
        - name: PORT
          value: "9555"
        - name: MAX_ADS_TO_SERVE
          value: "{{para.MAX_ADS_TO_SERVE}}"
        resources:
          requests:
            cpu: 200m
            memory: 180Mi
          limits:
            cpu: {{para.CPU_LIMIT}}m
            memory: {{para.MEMORY_LIMIT}}Mi
        readinessProbe:
          initialDelaySeconds: 20
          periodSeconds: 15
          exec:
            command: ["/bin/grpc_health_probe", "-addr=:9555"]
        livenessProbe:
          initialDelaySeconds: 20
          periodSeconds: 15
          exec:
            command: ["/bin/grpc_health_probe", "-addr=:9555"]
---
apiVersion: v1
kind: Service
metadata:
  name: adservice
spec:
  clusterIP: None
  selector:
    app: adservice
  ports:
  - name: grpc
    port: 9555
    targetPort: 9555
