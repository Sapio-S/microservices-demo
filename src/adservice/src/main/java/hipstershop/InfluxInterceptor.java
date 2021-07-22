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
import com.influxdb.client.WriteOptions;
import com.influxdb.client.domain.WritePrecision;
import com.influxdb.client.write.Point;
import com.influxdb.query.FluxRecord;
import com.influxdb.query.FluxTable;


public class InfluxInterceptor implements ServerInterceptor {

  private static final Logger logger = Logger.getLogger(InfluxInterceptor.class.getName());

  private static String token = "EHPNLGRTa1fwor7b9E0tjUHXw6EfHw1bl0yJ9LHuuoT7J7rUhXVQ-oAIq7vB9IIh6MJ9tT2-CFyqoTBRO9DzZg==";
  private static String org = "1205402283@qq.com";
  private static String bucket = "trace";
  private static InfluxDBClient influxDBClient;
  private static WriteApi writeApi;

  InfluxInterceptor(){
    this.influxDBClient = InfluxDBClientFactory.create("https://eastus-1.azure.cloud2.influxdata.com", this.token.toCharArray(), this.org, this.bucket);
    this.writeApi = this.influxDBClient.getWriteApi(WriteOptions.builder()
      .batchSize(500)
      .flushInterval(1000)
      .bufferLimit(10000)
      .jitterInterval(0)
      .retryInterval(5000)
      .build());
  }

  @Override
  public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(
      ServerCall<ReqT, RespT> call,
      final Metadata requestHeaders,
      ServerCallHandler<ReqT, RespT> next) {
    long start = System.nanoTime();

    // request header:
    // Metadata(content-type=application/grpc,user-agent=grpc-go/1.22.0,grpc-timeout=99983600n,grpc-trace-bin=AADjbauco/vdWIuBVyRmjY44AW7mHk/RJjkeAgA)

    ServerCall.Listener<ReqT> res = next.startCall(call, requestHeaders);

    long end = (System.nanoTime() - start)/1000;  // change into us
    Point point = Point.measurement("service_metric").addTag("pod", "adservice").addTag("service", "ad").addField("latency", end).time(Instant.now(), WritePrecision.NS);;
    this.writeApi.writePoint(point);
    return res;
  }
}