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

// if(process.env.DISABLE_PROFILER) {
//   console.log("Profiler disabled.")
// }
// else {
//   console.log("Profiler enabled.")
//   require('@google-cloud/profiler').start({
//     serviceContext: {
//       service: 'currencyservice',
//       version: '1.0.0'
//     }
//   });
// }


// if(process.env.DISABLE_TRACING) {
//   console.log("Tracing disabled.")
// }
// else {
//   console.log("Tracing enabled.")
//   require('@google-cloud/trace-agent').start();
// }

// if(process.env.DISABLE_DEBUGGER) {
//   console.log("Debugger disabled.")
// }
// else {
//   console.log("Debugger enabled.")
//   require('@google-cloud/debug-agent').start({
//     serviceContext: {
//       service: 'currencyservice',
//       version: 'VERSION'
//     }
//   });
// }
// import ExperimentalServer from 'ges';

// const ExperimentalServer = require('ges');
const path = require('path');
const grpc = require('grpc');
const interceptors = require('grpc-interceptors');
// const grpc = require('grpc-middleware');

const pino = require('pino');
const protoLoader = require('@grpc/proto-loader');

const MAIN_PROTO_PATH = path.join(__dirname, './proto/demo.proto');
const HEALTH_PROTO_PATH = path.join(__dirname, './proto/grpc/health/v1/health.proto');

const PORT = process.env.PORT;

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

// function preHook(context, request) {
//   console.log('in prehook');
//   context.time = new Date().getTime();
// } 

// function postHook(err, context, request) {
//   console.log('in postHook');
//   let end = new Date().getTime();
//   console.log(context);
//   console.log(end - context.time); // 时间戳格式
// } 

/**
 * Starts an RPC server that receives requests for the
 * CurrencyConverter service at the sample server port
 */


function main () {
  logger.info(`Starting gRPC server on port ${PORT}...`);

  // method 1
  // const server = new grpc.Server(null, preHook, postHook);


  // method 2
  // const server = new ExperimentalServer();

  // server.addService(shopProto.CurrencyService.service, {getSupportedCurrencies, convert});
  // server.addService(healthProto.Health.service, {check});
  
  // // interceptor
  // server.use(async (context, next) => {
  //   // preprocess
  //   const start = Date.now();
  //   try {
  //     await next();
  //   } finally {
  //     // postprocess
  //     const costtime = Date.now() - start;
  //     console.log('costtime is', costtime);
  //   }
  // });

  // method 3
  const server = interceptors.serverProxy(new grpc.Server());
  server.addService(shopProto.CurrencyService.service, {getSupportedCurrencies, convert});
  server.addService(healthProto.Health.service, {check});
  const myMiddlewareFunc = function (ctx, next) {

    // do stuff before call
    const start = Date.now();
    try {
      await next();
    } catch(err) {
      next();
    }
    
    // do stuff after call
    const costtime = Date.now() - start;
    console.log('costtime is', costtime);
  }

  server.use(myMiddlewareFunc);
  
  server.bind(`0.0.0.0:${PORT}`, grpc.ServerCredentials.createInsecure());
  server.start();
}

main();
