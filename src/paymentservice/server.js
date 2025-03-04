// Copyright 2018 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

const path = require('path');
const grpc = require('grpc');
const interceptors = require('@echo-health/grpc-interceptors');
const {InfluxDB, Point, HttpError} = require('@influxdata/influxdb-client')

const pino = require('pino');
const protoLoader = require('@grpc/proto-loader');

const charge = require('./charge');

const logger = pino({
  name: 'paymentservice-server',
  messageKey: 'message',
  changeLevelName: 'severity',
  useLevelLabels: true
});

const token = 'pNFkiKKMTEVV9fYn-vk21om5hGpbH1lwbnuCsengK0RagjE48468gcSerxQILPZcVTRrrGK4iJMtPRsW87kvqA==';
const org = 'msra';
const bucket = 'trace';
const client = new InfluxDB({url: 'http://10.0.0.29:8086', token: token})
const writeOptions = {
  batchSize: 2000, 
  flushInterval: 60000,
}
const writeApi = client.getWriteApi(org, bucket, 'ns', writeOptions)

function handleExit(signal) {
  writeApi.flush();
  writeApi.close();
  logger.info(`touching exit!`);
  process.exit(0);
}
process.on('SIGINT', handleExit);
process.on('SIGTERM', handleExit);

function getNanoSecTime() {
  var hrTime = process.hrtime();
  return hrTime[0] * 1000000000 + hrTime[1];
}

class HipsterShopServer {
  constructor (protoRoot, port = HipsterShopServer.PORT) {
    this.port = port;

    this.packages = {
      hipsterShop: this.loadProto(path.join(protoRoot, 'demo.proto')),
      health: this.loadProto(path.join(protoRoot, 'grpc/health/v1/health.proto'))
    };

    // this.server = new grpc.Server();
    this.server = interceptors.serverProxy(new grpc.Server());
    const myMiddlewareFunc = async function (ctx, next) {
      // do stuff before call
      const start = getNanoSecTime(); // gives precision in ns
  
      try{
        await next();
      }
      catch(e){
        console.log("error!");
      }

      // console.log(ctx);
      // do stuff after call
      const costtime = (getNanoSecTime() - start)/1000;
      if(ctx.call.request.hasOwnProperty("service")){ // probe check
  
      }
      else{ // charge
        const point = new Point('s').floatField("latency", costtime).tag("service", "paymentservice")
        // const point = new Point('service_metric').floatField("latency", costtime).tag("service", "paymentservice").tag("method", "charge").timestamp(new Date())
        writeApi.writePoint(point)
        // console.log(`latency ${costtime}`)
      }
      
    }
  
    this.server.use(myMiddlewareFunc);
 
    this.loadAllProtos(protoRoot);
  }

  /**
   * Handler for PaymentService.Charge.
   * @param {*} call  { ChargeRequest }
   * @param {*} callback  fn(err, ChargeResponse)
   */
  static ChargeServiceHandler (call, callback) {
    try {
      logger.info(`PaymentService#Charge invoked with request ${JSON.stringify(call.request)}`);
      const response = charge(call.request);
      callback(null, response);
    } catch (err) {
      console.warn(err);
      callback(err);
    }
  }

  static CheckHandler (call, callback) {
    callback(null, { status: 'SERVING' });
  }

  listen () {
    this.server.bind(`0.0.0.0:${this.port}`, grpc.ServerCredentials.createInsecure());
    logger.info(`PaymentService grpc server listening on ${this.port}`);
    this.server.start();
  }

  loadProto (path) {
    const packageDefinition = protoLoader.loadSync(
      path,
      {
        keepCase: true,
        longs: String,
        enums: String,
        defaults: true,
        oneofs: true
      }
    );
    return grpc.loadPackageDefinition(packageDefinition);
  }

  loadAllProtos (protoRoot) {
    const hipsterShopPackage = this.packages.hipsterShop.hipstershop;
    const healthPackage = this.packages.health.grpc.health.v1;

    this.server.addService(
      hipsterShopPackage.PaymentService.service,
      {
        charge: HipsterShopServer.ChargeServiceHandler.bind(this)
      }
    );

    this.server.addService(
      healthPackage.Health.service,
      {
        check: HipsterShopServer.CheckHandler.bind(this)
      }
    );
  }
}

HipsterShopServer.PORT = process.env.PORT;

module.exports = HipsterShopServer;
