import time

from datetime import datetime

from influxdb_client import InfluxDBClient, Point, WritePrecision, WriteOptions
from influxdb_client.client.write_api import ASYNCHRONOUS
from grpc_interceptor import ServerInterceptor
class InfluxInterceptor(ServerInterceptor):

    def __init__(self, name):
        self.service = name
        self.write_api = InfluxDBClient(url="https://eastus-1.azure.cloud2.influxdata.com", 
                                        token = "EHPNLGRTa1fwor7b9E0tjUHXw6EfHw1bl0yJ9LHuuoT7J7rUhXVQ-oAIq7vB9IIh6MJ9tT2-CFyqoTBRO9DzZg==", 
                                        org="1205402283@qq.com").write_api(write_options=WriteOptions(batch_size=200,
                                                                                                        flush_interval=10_000,
                                                                                                        jitter_interval=2_000,
                                                                                                        retry_interval=5_000,
                                                                                                        max_retries=5,
                                                                                                        max_retry_delay=30_000,
                                                                                                        exponential_base=2))
        
    
    # for grpc.ServerInterceptor

    # def intercept_service(self, continuation, handler_call_details):
    #     start = time.time_ns()
    #     res = continuation(handler_call_details)
    #     end = time.time_ns()
    #     latency = int((end - start)/1000)
    #     print(handler_call_details.method)
    #     print(latency)
    #     p = Point(self.service).field("latency", latency)
    #     self.write_api.write(bucket="trace", record=p)
    #     return res
    
    def intercept(selfmethod_name):
        start = time.time_ns()
        # res = method(request, context)
        end = time.time_ns()
        latency = int((end - start)/1000)
        if method_name == "/grpc.health.v1.Health/Check":
            return res
        # p = Point(self.service).field(method_name, latency) # health probe: "/grpc.health.v1.Health/Check"
        p = Point("service_metric") \
            .tag("service", self.service) \
            .field("latency", latency) \
            .tag("method", method_name) \
            .time(datetime.utcnow(), WritePrecision.NS)
        self.write_api.write(bucket="trace", record=p)
        return res
    # def run(self):
    #     self.intercept_service()

inter = InfluxInterceptor("python test")
for i in range(5):
    inter.intercept("test")