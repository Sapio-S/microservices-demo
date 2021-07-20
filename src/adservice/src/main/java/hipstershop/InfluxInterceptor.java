package hipstershop;

import com.google.common.annotations.VisibleForTesting;
import io.grpc.ForwardingServerCall.SimpleForwardingServerCall;
import io.grpc.Metadata;
import io.grpc.ServerCall;
import io.grpc.ServerCallHandler;
import io.grpc.ServerInterceptor;
import java.util.logging.Logger;
import java.util.Date;
import java.time.Instant;
import java.util.List;

import com.influxdb.annotations.Column;
import com.influxdb.annotations.Measurement;
import com.influxdb.client.InfluxDBClient;
import com.influxdb.client.InfluxDBClientFactory;
import com.influxdb.client.QueryApi;
import com.influxdb.client.WriteApi;
import com.influxdb.client.domain.WritePrecision;
import com.influxdb.client.write.Point;
import com.influxdb.query.FluxRecord;
import com.influxdb.query.FluxTable;


public class InfluxInterceptor implements ServerInterceptor {

  private static final Logger logger = Logger.getLogger(InfluxInterceptor.class.getName());

  private static char[] token = "nMbCj1HHoEV5UTcZBBrtm6kkQ4xzlK8I0EfRrZO2i6ngr3mBB4y0XLUQvBdxTZCnHDoHZQgaNRGbhfSZ9A76fQ==".toCharArray();
  private static String org = "MSRA";
  private static String bucket = "trace";


      public static void write2influx(long t) {

        InfluxDBClient influxDBClient = InfluxDBClientFactory.create("http://localhost:8086", token, org, bucket);

        //
        // Write data
        //
        try (WriteApi writeApi = influxDBClient.getWriteApi()) {

            //
            // Write by Data Point
            //
            Point point = Point.measurement("ad service")
                    .addField("latency", t)
                    .time(Instant.now().toEpochMilli(), WritePrecision.MS);
            writeApi.writePoint(point);
        }
        influxDBClient.close();
    }

  @Override
  public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(
      ServerCall<ReqT, RespT> call,
      final Metadata requestHeaders,
      ServerCallHandler<ReqT, RespT> next) {
    logger.info("header received from client:" + requestHeaders);
    long start = System.nanoTime();
    ServerCall.Listener<ReqT> res = next.startCall(call, requestHeaders);
    long end = System.nanoTime() - start;
    logger.info("latency is "+Long.toString(end / 1000)); // change into ms
    // write2influx(end-start);
    return res;
  }
}