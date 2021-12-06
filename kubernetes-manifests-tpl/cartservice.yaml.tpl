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
  name: cartservice
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cartservice
  template:
    metadata:
      labels:
        app: cartservice
    spec:
      serviceAccountName: default
      terminationGracePeriodSeconds: 5
      securityContext:
        sysctls:
        - name: net.ipv4.tcp_rmem
          value: "4096        {{para.IPV4_RMEM}}  6291456"
        - name: net.ipv4.tcp_wmem
          value: "4096        {{para.IPV4_WMEM}}   4194304"
      initContainers:
        - name: db-probe
          image: simonalphafang/alpine-telnet:0.0.1
          command:
          - sh
          - -c
          - |
            set -e
            export ADDR="redis-cart.default.svc.cluster.local"
            while true; do
              echo '' | telnet $ADDR 6379
              break
              sleep 3
            done
      containers:
      - name: server
        image: cartservice
        ports:
        - containerPort: 7070
        env:
        - name: REDIS_ADDR
          value: "redis-cart:6379"
        - name: maxmemory
          value: "{{para.maxmemory}}MB"
        - name: maxmemory_samples
          value: "{{para.maxmemory_samples}}"
        - name: hash_max_ziplist_entries
          value: "{{para.hash_max_ziplist_entries}}"
        resources:
          requests:
            cpu: 200m
            memory: 64Mi
          limits:
            cpu: {{para.CPU_LIMIT}}m
            memory: {{para.MEMORY_LIMIT}}Mi
        readinessProbe:
          initialDelaySeconds: 15
          exec:
            command: ["/bin/grpc_health_probe", "-addr=:7070", "-rpc-timeout=5s"]
        livenessProbe:
          initialDelaySeconds: 15
          periodSeconds: 10
          exec:
            command: ["/bin/grpc_health_probe", "-addr=:7070", "-rpc-timeout=5s"]
---
apiVersion: v1
kind: Service
metadata:
  name: cartservice
spec:
  clusterIP: None
  selector:
    app: cartservice
  ports:
  - name: grpc
    port: 7070
    targetPort: 7070
