import grpc
import time

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

class InfluxInterceptor(grpc.ServerInterceptor):

    def __init__(self, name):
        self.service = name
        self.cnt = 0
        self.total = 0
        self.points = []
        self.write_api = InfluxDBClient(url="http://localhost:8086", token="nMbCj1HHoEV5UTcZBBrtm6kkQ4xzlK8I0EfRrZO2i6ngr3mBB4y0XLUQvBdxTZCnHDoHZQgaNRGbhfSZ9A76fQ==", org="MSRA").write_api(write_options=SYNCHRONOUS)
        

    def intercept_service(self, continuation, handler_call_details):
        start = time.time()
        res = continuation(handler_call_details)
        end = time.time()
        latency = end - start
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