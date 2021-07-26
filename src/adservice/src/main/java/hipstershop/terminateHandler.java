package hipstershop;

import sun.misc.Signal;
import sun.misc.SignalHandler;

import com.influxdb.client.InfluxDBClient;
import com.influxdb.client.WriteApi;

public class terminateHandler implements SignalHandler {
    
    private static InfluxDBClient influxDBClient;
    private static WriteApi writeApi;

	public terminateHandler(WriteApi writeApi_, InfluxDBClient influxDBClient_) {
        this.writeApi = writeApi_;
        this.influxDBClient = influxDBClient_;
    }

    @Override  
    public void handle(Signal signal) {  
        if ( signal.getName().equals("TERM") || signal.getName().equals("INT")) {
            this.writeApi.flush();
            this.influxDBClient.close();
            System.exit(-1);
        }  
    } 
}