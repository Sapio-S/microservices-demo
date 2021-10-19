# import grpc
import time

from datetime import datetime

from influxdb_client import InfluxDBClient, Point, WritePrecision, WriteOptions
from influxdb_client.client.write_api import ASYNCHRONOUS
from grpc_interceptor import ServerInterceptor
import sys
import signal
class InfluxInterceptor(ServerInterceptor):

    def __init__(self, name, podName):
        signal.signal(signal.SIGINT, self.close_program)
        signal.signal(signal.SIGTERM, self.close_program)
        self.service = name
        self.pod = podName
        self.client = InfluxDBClient(url="http://10.0.0.29:8086", 
                                        token = "pNFkiKKMTEVV9fYn-vk21om5hGpbH1lwbnuCsengK0RagjE48468gcSerxQILPZcVTRrrGK4iJMtPRsW87kvqA==", 
                                        org="msra")
        self.write_api = self.client.write_api(write_options=WriteOptions(batch_size=2000,
                                                                        flush_interval=60_000))
        
    def close_program(self, *args):
        self.write_api.flush()
        self.client.close()
        print(args)
        print("closing...")
        sys.exit(0)
    
    def intercept(self,method,request,context,method_name):
        start = time.time_ns()
        res = method(request, context)
        end = time.time_ns()
        latency = int((end - start)/1000)
        if method_name == "/grpc.health.v1.Health/Check":
            return res
        # p = Point(self.service).field(method_name, latency) # health probe: "/grpc.health.v1.Health/Check"
        p = Point("service_metric") \
            .tag("service", self.service) \
            .field("latency", latency) \
            .tag("method", method_name) \
            .tag("podname", self.pod) \
            .time(datetime.utcnow(), WritePrecision.NS)
        self.write_api.write(bucket="trace", record=p)
        return res

        """Override this method to implement a custom interceptor.
         You should call method(request, context) to invoke the
         next handler (either the RPC method implementation, or the
         next interceptor in the list).
         Args:
             method: The next interceptor, or method implementation.
             request: The RPC request, as a protobuf message.
             context: The ServicerContext pass by gRPC to the service.
             method_name: A string of the form
                 "/protobuf.package.Service/Method"
         Returns:
             This should generally return the result of
             method(request, context), which is typically the RPC
             method response, as a protobuf message. The interceptor
             is free to modify this in some way, however.
         """
        
    
