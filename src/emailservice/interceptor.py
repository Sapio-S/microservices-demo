import grpc
import time
from datetime import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

class InfluxInterceptor(grpc.ServerInterceptor):

    def __init__(self, name):
        self.service = name
        self.cnt = 0
        self.total = 0
        self.points = []
        

    def intercept_service(self, continuation, handler_call_details):
        start = time.time_ns()
        res = continuation(handler_call_details)
        print(res)
        end = time.time_ns()
        latency = int((end - start)/1000)
        self.cnt += 1
        self.total += 1
        p = Point(self.service).field("latency", latency)
        self.points.append(p)
        print(latency)
        # if self.cnt > 0:
        #     self.write2influx()
        return res

    def write2influx(self):
        self.write_api = InfluxDBClient(url="http://localhost:8086", token="nMbCj1HHoEV5UTcZBBrtm6kkQ4xzlK8I0EfRrZO2i6ngr3mBB4y0XLUQvBdxTZCnHDoHZQgaNRGbhfSZ9A76fQ==", org="MSRA").write_api(write_options=SYNCHRONOUS)
        
        for p in self.points:
            print("?")
            self.write_api.write(bucket="trace", record=p).time(datetime.utcnow().replace(minute=0, second=0, microsecond=0))
            print("!")
        self.write_api.flush()
        # print("sent")
        # print(points)
        self.cnt = 0
        self.points = []