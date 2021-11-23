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
import sun.misc.Signal;
import sun.misc.SignalHandler;
public class InfluxInterceptor implements ServerInterceptor {

  private static final Logger logger = Logger.getLogger(InfluxInterceptor.class.getName());

  private static String token = "b-M3xpZbjd9kVVf8DlQ8hAlAwc-ttyn12Ewhh1evVg7034k330Ox1PRIBHiuZ5Pum8g56Cjt-pD-s36UNg8JjQ==";
  private static String org = "msra";
  private static String bucket = "trace";
  private static InfluxDBClient influxDBClient;
  private static WriteApi writeApi;

  InfluxInterceptor(){
    this.influxDBClient = InfluxDBClientFactory.create("http://10.0.0.29:8086", this.token.toCharArray(), this.org, this.bucket);
    this.writeApi = this.influxDBClient.getWriteApi(WriteOptions.builder()
      .batchSize(2000)
      .flushInterval(60000)
      .build());
    terminateHandler handler = new terminateHandler(this.writeApi, this.influxDBClient);
    Signal.handle(new Signal("INT"), handler);
    Signal.handle(new Signal("TERM"), handler);
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
    Point point = Point.measurement("service_metric").addTag("pod", "adservice").addTag("service", "adservice").addField("latency", end).time(Instant.now(), WritePrecision.NS);;
    this.writeApi.writePoint(point);
    return res;
  }
}