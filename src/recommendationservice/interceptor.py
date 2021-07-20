# import grpc
import time

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from grpc_interceptor import ServerInterceptor

class InfluxInterceptor(ServerInterceptor):

    def __init__(self, name):
        self.service = name
        self.cnt = 0
        self.total = 0
        self.points = []
        self.write_api = InfluxDBClient(url="http://localhost:8086", token="nMbCj1HHoEV5UTcZBBrtm6kkQ4xzlK8I0EfRrZO2i6ngr3mBB4y0XLUQvBdxTZCnHDoHZQgaNRGbhfSZ9A76fQ==", org="MSRA").write_api(write_options=SYNCHRONOUS)
        

    def intercept_service(self, continuation, handler_call_details):
        start = time.time_ns()
        res = continuation(handler_call_details)
        end = time.time_ns()
        latency = int((end - start)/1000)
        self.cnt += 1
        self.total += 1
        p = Point(self.service).tag("lat_tag", str(self.total)).field("latency", latency)
        self.points.append(p)
        print(latency)
        # if self.cnt > 0:
        #     self.write2influx()
        return res

    def write2influx(self):
        for p in self.points:
            print("?")
            self.write_api.write(bucket="trace", record=p)
            print("!")
        print("sent")
        print(points)
        self.cnt = 0
        self.points = []
    
    def intercept(
        self,
        method,
        request,
        context,
        method_name,
    ):
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
        start = time.time_ns()
        res = method(request, context)
        end = time.time_ns()
        latency = end - start
        self.cnt += 1
        self.total += 1
        p = Point(self.service).tag("lat_tag", str(self.total)).field("latency", latency)
        self.points.append(p)
        print(latency)
        # if self.cnt > 0:
        #     self.write2influx()
        return res
        # try:
        #     return 
        # except GrpcException as e:
        #     context.set_code(e.status_code)
        #     context.set_details(e.details)
        #     raise