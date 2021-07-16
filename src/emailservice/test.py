# import grpc
import time

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

class InfluxInterceptor():

    def __init__(self, name):
        self.service = name
        self.cnt = 0
        self.points = []
        

    def intercept_service(self):
        start = time.time()
        # res = continuation(handler_call_details)
        end = time.time()
        latency = end - start
        print(latency)
        p = Point(self.service).field("latency", latency)
        self.points.append(p)
        if self.cnt > 0:
            self.write2influx()
        return 0

    def write2influx():
        self.write_api = InfluxDBClient(url="http://localhost:8086", token="nMbCj1HHoEV5UTcZBBrtm6kkQ4xzlK8I0EfRrZO2i6ngr3mBB4y0XLUQvBdxTZCnHDoHZQgaNRGbhfSZ9A76fQ==", org="MSRA").write_api(write_options=SYNCHRONOUS)
        self.write_api.write(bucket="trace", record=self.points)
        cnt = 0
    # def run(self):
    #     self.intercept_service()

inter = InfluxInterceptor("python test")
for i in range(5):
    inter.intercept_service()