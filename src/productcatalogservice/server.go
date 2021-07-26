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

package main

import (
	"bytes"
	"context"
	"flag"
	"fmt"
	"io/ioutil"
	"net"
	"os"
	"os/signal"
	"strings"
	"sync"
	"syscall"
	"time"
	// "common"

	pb "github.com/GoogleCloudPlatform/microservices-demo/src/productcatalogservice/genproto"
	healthpb "google.golang.org/grpc/health/grpc_health_v1"

	// "cloud.google.com/go/profiler"
	// "contrib.go.opencensus.io/exporter/jaeger"
	// "contrib.go.opencensus.io/exporter/stackdriver"
	"github.com/golang/protobuf/jsonpb"
	"github.com/sirupsen/logrus"
	//  "go.opencensus.io/exporter/jaeger"
	// "go.opencensus.io/plugin/ocgrpc"
	// "go.opencensus.io/stats/view"
	// "go.opencensus.io/trace"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"

	// "github.com/grpc-ecosystem/grpc-opentracing/go/otgrpc"
	// "github.com/opentracing/opentracing-go"

	// influxdb2 "github.com/influxdata/influxdb-client-go/v2"
	// "github.com/influxdata/influxdb-client-go/v2/api"

	"github.com/influxdata/influxdb-client-go/v2"
)

var (
	cat          pb.ListProductsResponse
	catalogMutex *sync.Mutex
	log          *logrus.Logger
	extraLatency time.Duration

	port = "3550"

	reloadCatalog bool

	// writeAPI 	 api.WriteAPI
)

// type Server struct {
// 	users map[string]string

// 	Tracer       opentracing.Tracer
// 	// Registry     *registry.Client
// 	Port         int
// 	IpAddr       string
// 	// MongoSession *mgo.Session
// 	Monitor      *common.MonitoringHelper
// }

const name = "product catalog service"

func init() {
	log = logrus.New()
	log.Formatter = &logrus.JSONFormatter{
		FieldMap: logrus.FieldMap{
			logrus.FieldKeyTime:  "timestamp",
			logrus.FieldKeyLevel: "severity",
			logrus.FieldKeyMsg:   "message",
		},
		TimestampFormat: time.RFC3339Nano,
	}
	log.Out = os.Stdout
	catalogMutex = &sync.Mutex{}
	err := readCatalogFile(&cat)
	if err != nil {
		log.Warnf("could not parse product catalog")
	}
}

func main() {
	flag.Parse()

	// set injected latency
	if s := os.Getenv("EXTRA_LATENCY"); s != "" {
		v, err := time.ParseDuration(s)
		if err != nil {
			log.Fatalf("failed to parse EXTRA_LATENCY (%s) as time.Duration: %+v", v, err)
		}
		extraLatency = v
		log.Infof("extra latency enabled (duration: %v)", extraLatency)
	} else {
		extraLatency = time.Duration(0)
	}

	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGUSR1, syscall.SIGUSR2)
	go func() {
		for {
			sig := <-sigs
			log.Printf("Received signal: %s", sig)
			if sig == syscall.SIGUSR1 {
				reloadCatalog = true
				log.Infof("Enable catalog reloading")
			} else {
				reloadCatalog = false
				log.Infof("Disable catalog reloading")
			}
		}
	}()

	if os.Getenv("PORT") != "" {
		port = os.Getenv("PORT")
	}
	log.Infof("starting grpc server at :%s", port)
	run(port)
	select {}
}

const token = "EHPNLGRTa1fwor7b9E0tjUHXw6EfHw1bl0yJ9LHuuoT7J7rUhXVQ-oAIq7vB9IIh6MJ9tT2-CFyqoTBRO9DzZg=="
const bucket = "trace"
const org = "1205402283@qq.com"

// Authorization unary interceptor function to handle authorize per RPC call
func serverInterceptor(ctx context.Context,
	req interface{},
	info *grpc.UnaryServerInfo,
	handler grpc.UnaryHandler) (interface{}, error) {

	start := time.Now()
	// Calls the handler
	h, err := handler(ctx, req)
	log.Info(req)

	end := time.Now()
	duration := end.Sub(start).Microseconds()
	log.Info("latency", duration)
	log.Info(ctx)

	client := influxdb2.NewClientWithOptions("https://eastus-1.azure.cloud2.influxdata.com", token, 
		influxdb2.DefaultOptions().
		SetBatchSize(100).
		SetFlushInterval(1000))
	writeAPI := client.WriteAPI(org, bucket)
	p := influxdb2.NewPointWithMeasurement("service_metric").AddField("latency", duration).AddTag("service", "productcatalogservice").AddTag("method", info.FullMethod).SetTime(time.Now())
	// write point asynchronously
	writeAPI.WritePoint(p)
	return h, err
}

func withServerUnaryInterceptor() grpc.ServerOption {
	return grpc.UnaryInterceptor(serverInterceptor)
}

func run(port string) string {
	l, err := net.Listen("tcp", fmt.Sprintf(":%s", port))


	if err != nil {
		log.Fatal(err)
	}
	var srv *grpc.Server

	// keepaliveTimeout, _ := strconv.Atoi(common.GetCfgData(common.CfgKeySvrTimeout, nil))

	// opts := []grpc.ServerOption{
	// 	grpc.KeepaliveParams(keepalive.ServerParameters{
	// 		Timeout: time.Duration(keepaliveTimeout) * time.Second,
	// 	}),
	// 	grpc.KeepaliveEnforcementPolicy(keepalive.EnforcementPolicy{
	// 		PermitWithoutStream: true,
	// 	}),
	// 	grpc.UnaryInterceptor(grpc_middleware.ChainUnaryServer(
	// 		// grpc_prometheus.UnaryServerInterceptor,
	// 		s.Monitor.MetricInterceptor(),
	// 		otgrpc.OpenTracingServerInterceptor(s.Tracer),
	// 	)),
	// }

	// if tlsopt := tls.GetServerOpt(); tlsopt != nil {
	// 	opts = append(opts, tlsopt)
	// }

	// srv := grpc.NewServer(opts...)

	srv = grpc.NewServer(
		withServerUnaryInterceptor(),
	)
	// ref: https://shijuvar.medium.com/writing-grpc-interceptors-in-go-bf3e7671fe48

	// if os.Getenv("DISABLE_STATS") == "" {
	// 	log.Info("Stats enabled.")
	// 	srv = grpc.NewServer(grpc.StatsHandler(&ocgrpc.ServerHandler{}))
	// } else {
	// 	log.Info("Stats disabled.")
	// 	srv = grpc.NewServer()
	// }

	// srv = grpc.NewServer()

	svc := &productCatalog{}

	pb.RegisterProductCatalogServiceServer(srv, svc)
	healthpb.RegisterHealthServer(srv, svc)
	go srv.Serve(l)
	return l.Addr().String()
}

type productCatalog struct{}

func readCatalogFile(catalog *pb.ListProductsResponse) error {
	catalogMutex.Lock()
	defer catalogMutex.Unlock()
	catalogJSON, err := ioutil.ReadFile("products.json")
	if err != nil {
		log.Fatalf("failed to open product catalog json file: %v", err)
		return err
	}
	if err := jsonpb.Unmarshal(bytes.NewReader(catalogJSON), catalog); err != nil {
		log.Warnf("failed to parse the catalog JSON: %v", err)
		return err
	}
	log.Info("successfully parsed product catalog json")
	return nil
}

func parseCatalog() []*pb.Product {
	if reloadCatalog || len(cat.Products) == 0 {
		err := readCatalogFile(&cat)
		if err != nil {
			return []*pb.Product{}
		}
	}
	return cat.Products
}

func (p *productCatalog) Check(ctx context.Context, req *healthpb.HealthCheckRequest) (*healthpb.HealthCheckResponse, error) {
	return &healthpb.HealthCheckResponse{Status: healthpb.HealthCheckResponse_SERVING}, nil
}

func (p *productCatalog) Watch(req *healthpb.HealthCheckRequest, ws healthpb.Health_WatchServer) error {
	return status.Errorf(codes.Unimplemented, "health check via Watch not implemented")
}

func (p *productCatalog) ListProducts(context.Context, *pb.Empty) (*pb.ListProductsResponse, error) {
	time.Sleep(extraLatency)
	return &pb.ListProductsResponse{Products: parseCatalog()}, nil
}

func (p *productCatalog) GetProduct(ctx context.Context, req *pb.GetProductRequest) (*pb.Product, error) {
	time.Sleep(extraLatency)
	var found *pb.Product
	for i := 0; i < len(parseCatalog()); i++ {
		if req.Id == parseCatalog()[i].Id {
			found = parseCatalog()[i]
		}
	}
	if found == nil {
		return nil, status.Errorf(codes.NotFound, "no product with ID %s", req.Id)
	}
	return found, nil
}

func (p *productCatalog) SearchProducts(ctx context.Context, req *pb.SearchProductsRequest) (*pb.SearchProductsResponse, error) {
	time.Sleep(extraLatency)
	// Intepret query as a substring match in name or description.
	var ps []*pb.Product
	for _, p := range parseCatalog() {
		if strings.Contains(strings.ToLower(p.Name), strings.ToLower(req.Query)) ||
			strings.Contains(strings.ToLower(p.Description), strings.ToLower(req.Query)) {
			ps = append(ps, p)
		}
	}
	return &pb.SearchProductsResponse{Results: ps}, nil
}
