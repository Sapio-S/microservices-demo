/*
 * Copyright 2018 Google LLC.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

const path = require('path');
const grpc = require('grpc');
const interceptors = require('@echo-health/grpc-interceptors');
const {InfluxDB, Point, HttpError} = require('@influxdata/influxdb-client')
// const process = require('process');
const pino = require('pino');
const protoLoader = require('@grpc/proto-loader');

const MAIN_PROTO_PATH = path.join(__dirname, './proto/demo.proto');
const HEALTH_PROTO_PATH = path.join(__dirname, './proto/grpc/health/v1/health.proto');

const PORT = process.env.PORT;
const podname=process.env.HOSTNAME;

const shopProto = _loadProto(MAIN_PROTO_PATH).hipstershop;
const healthProto = _loadProto(HEALTH_PROTO_PATH).grpc.health.v1;

const logger = pino({
  name: 'currencyservice-server',
  messageKey: 'message',
  changeLevelName: 'severity',
  useLevelLabels: true
});


/**
 * Helper function that loads a protobuf file.
 */
function _loadProto (path) {
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

/**
 * Helper function that gets currency data from a stored JSON file
 * Uses public data from European Central Bank
 */
function _getCurrencyData (callback) {
  const data = require('./data/currency_conversion.json');
  callback(data);
}

/**
 * Helper function that handles decimal/fractional carrying
 */
function _carry (amount) {
  const fractionSize = Math.pow(10, 9);
  amount.nanos += (amount.units % 1) * fractionSize;
  amount.units = Math.floor(amount.units) + Math.floor(amount.nanos / fractionSize);
  amount.nanos = amount.nanos % fractionSize;
  return amount;
}

/**
 * Lists the supported currencies
 */
function getSupportedCurrencies (call, callback) {
  logger.info('Getting supported currencies...');
  _getCurrencyData((data) => {
    callback(null, {currency_codes: Object.keys(data)});
  });
}

/**
 * Converts between currencies
 */
function convert (call, callback) {
  logger.info('received conversion request');
  try {
    _getCurrencyData((data) => {
      const request = call.request;

      // Convert: from_currency --> EUR
      const from = request.from;
      const euros = _carry({
        units: from.units / data[from.currency_code],
        nanos: from.nanos / data[from.currency_code]
      });

      euros.nanos = Math.round(euros.nanos);

      // Convert: EUR --> to_currency
      const result = _carry({
        units: euros.units * data[request.to_code],
        nanos: euros.nanos * data[request.to_code]
      });

      result.units = Math.floor(result.units);
      result.nanos = Math.floor(result.nanos);
      result.currency_code = request.to_code;

      logger.info(`conversion request successful`);
      callback(null, result);
    });
  } catch (err) {
    logger.error(`conversion request failed: ${err}`);
    callback(err.message);
  }
}

/**
 * Endpoint for health checks
 */
function check (call, callback) {
  callback(null, { status: 'SERVING' });
}

function getNanoSecTime() {
  var hrTime = process.hrtime();
  return hrTime[0] * 1000000000 + hrTime[1];
}
const token = 'b-M3xpZbjd9kVVf8DlQ8hAlAwc-ttyn12Ewhh1evVg7034k330Ox1PRIBHiuZ5Pum8g56Cjt-pD-s36UNg8JjQ==';
const org = 'msra';
const bucket = 'trace';
const client = new InfluxDB({url: 'http://10.0.0.29:8086', token: token})
const writeOptions = {
  batchSize: 200, 
  flushInterval: 1000,
}
const writeApi = client.getWriteApi(org, bucket, 'ns', writeOptions)

function handleExit(signal) {
  writeApi.flush();
  writeApi.close();
  process.exit(0);
}
process.on('SIGINT', handleExit);
process.on('SIGTERM', handleExit);

function main () {
  logger.info(`Starting gRPC server on port ${PORT}...`);

  const server = interceptors.serverProxy(new grpc.Server());

  server.addService(shopProto.CurrencyService.service, {getSupportedCurrencies, convert});
  server.addService(healthProto.Health.service, {check});

  const myMiddlewareFunc = async function (ctx, next) {
    // do stuff before call
    const start = getNanoSecTime(); // gives precision in ns

    try{
      await next();
    }
    catch(e){
      console.log("error!");
    }
    // do stuff after call
    const costtime = (getNanoSecTime() - start)/1000;
    if(ctx.call.request.hasOwnProperty("service")){ // probe check

    }
    else if(ctx.call.request.hasOwnProperty("from")){ // conversion
      const point = new Point('service_metric').intField("latency", costtime).tag("podname", podname).tag("service", "currencyservice").tag("method", "conversion").timestamp(new Date())
      writeApi.writePoint(point)
      // console.log(`latency ${costtime}`)
    }
    else{ // getSupportedCurrencies
      const point = new Point('service_metric').intField("latency", costtime).tag("podname", podname).tag("service", "currencyservice").tag("method", "get currency").timestamp(new Date())
      writeApi.writePoint(point)
      // console.log(`latency ${costtime}`)
    }
    
  }

  server.use(myMiddlewareFunc);
  
  server.bind(`0.0.0.0:${PORT}`, grpc.ServerCredentials.createInsecure());
  server.start();
}

main();
