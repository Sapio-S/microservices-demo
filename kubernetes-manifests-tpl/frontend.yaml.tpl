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
  name: frontend
spec:
  replicas: 1
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
      annotations:
        sidecar.istio.io/rewriteAppHTTPProbers: "true"
    spec:
      securityContext:
        sysctls:
        - name: net.ipv4.tcp_rmem
          value: "4096        {{para.IPV4_RMEM}}  6291456"
        - name: net.ipv4.tcp_wmem
          value: "4096        {{para.IPV4_WMEM}}   4194304"
      serviceAccountName: default
      initContainers:
        - name: db-probe
          image: simonalphafang/alpine-telnet:0.0.1
          command:
          - sh
          - -c
          - |
            set -e
            export ADDR1="shippingservice.default.svc.cluster.local"
            export ADDR2="adservice.default.svc.cluster.local"
            export ADDR3="cartservice.default.svc.cluster.local"
            export ADDR4="checkoutservice.default.svc.cluster.local"
            export ADDR5="currencyservice.default.svc.cluster.local"
            export ADDR6="productcatalogservice.default.svc.cluster.local"
            export ADDR7="recommendationservice.default.svc.cluster.local"
            while true; do
              echo '' | telnet $ADDR1 50051 && \
              echo '' | telnet $ADDR2 9555 && \
              echo '' | telnet $ADDR3 7070 && \
              echo '' | telnet $ADDR4 5050 && \
              echo '' | telnet $ADDR5 7000 && \
              echo '' | telnet $ADDR7 8080 && \
              echo '' | telnet $ADDR6 3550
              break
              sleep 3
            done
      containers:
        - name: server
          image: frontend
          ports:
          - containerPort: 8080
          readinessProbe:
            initialDelaySeconds: 10
            httpGet:
              path: "/_healthz"
              port: 8080
              httpHeaders:
              - name: "Cookie"
                value: "shop_session-id=x-readiness-probe"
          livenessProbe:
            initialDelaySeconds: 10
            httpGet:
              path: "/_healthz"
              port: 8080
              httpHeaders:
              - name: "Cookie"
                value: "shop_session-id=x-liveness-probe"
          env:
          - name: PORT
            value: "8080"
          - name: PRODUCT_CATALOG_SERVICE_ADDR
            value: "productcatalogservice:3550"
          - name: CURRENCY_SERVICE_ADDR
            value: "currencyservice:7000"
          - name: CART_SERVICE_ADDR
            value: "cartservice:7070"
          - name: RECOMMENDATION_SERVICE_ADDR
            value: "recommendationservice:8080"
          - name: SHIPPING_SERVICE_ADDR
            value: "shippingservice:50051"
          - name: CHECKOUT_SERVICE_ADDR
            value: "checkoutservice:5050"
          - name: AD_SERVICE_ADDR
            value: "adservice:9555"
          - name: GOGC
            value: "20"
          - name: GOMAXPROCS
            value: "4"
          resources:
            requests:
              cpu: 100m
              memory: 64Mi
            limits:
              cpu: {{para.CPU_LIMIT}}m
              memory: {{para.MEMORY_LIMIT}}Mi
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
spec:
  type: ClusterIP
  selector:
    app: frontend
  ports:
  - name: http
    port: 80
    targetPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-external
spec:
  type: LoadBalancer
  selector:
    app: frontend
  ports:
  - name: http
    port: 80
    targetPort: 8080
