using System;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Grpc.Core;
using StackExchange.Redis;
using Google.Protobuf;
using System.Collections.Generic;

using InfluxDB.Client;
using InfluxDB.Client.Api.Domain;
using InfluxDB.Client.Core;
using InfluxDB.Client.Writes;

namespace cartservice.cartstore
{
    public class RedisCartStore : ICartStore
    {
        private const string CART_FIELD_NAME = "cart";
        private const int REDIS_RETRY_NUM = 5;

        private volatile ConnectionMultiplexer redis;
        private volatile bool isRedisConnectionOpened = false;

        private readonly object locker = new object();
        private readonly byte[] emptyCartBytes;
        private readonly string connectionString;

        private string maxmemory;
        private string maxmemory_samples;
        private string hash_max_ziplist_entries;

        // const string token = "EHPNLGRTa1fwor7b9E0tjUHXw6EfHw1bl0yJ9LHuuoT7J7rUhXVQ-oAIq7vB9IIh6MJ9tT2-CFyqoTBRO9DzZg==";
        const string bucket = "trace";
        const string org = "msra";
        private readonly ConfigurationOptions redisConnectionOptions;

        private InfluxDBClient influxclient;
        private WriteApi writeApi0;
        public void initInflux(){
            this.influxclient = InfluxDBClientFactory.Create("http://10.0.0.51:8086", "2kmAK9DbfrhFA-nojNc1DKk3q8wQ4a14SnmMdVOjvBfsgTH_saoqvCUaZXuW3CBMyW2tIlew-zud2p6jKSboPg==");
            var options = InfluxDB.Client.WriteOptions.CreateNew()
                .BatchSize(2000)
                .FlushInterval(60000)
                .Build();
            this.writeApi0 = this.influxclient.GetWriteApi(options);
        }

        public void Write2Influx(PointData p){
            writeApi0.WritePoint(bucket, org, p);
        }

        public RedisCartStore(string redisAddress, string maxmemory_, string maxmemory_samples_, string hash_max_ziplist_entries_)
        {
            // Serialize empty cart into byte array.
            var cart = new Hipstershop.Cart();
            emptyCartBytes = cart.ToByteArray();
            connectionString = $"{redisAddress},ssl=false,allowAdmin=true,connectRetry=5,abortConnect=false";

            redisConnectionOptions = ConfigurationOptions.Parse(connectionString);

            // Try to reconnect if first retry failed (up to 5 times with exponential backoff)
            redisConnectionOptions.ConnectRetry = REDIS_RETRY_NUM;
            redisConnectionOptions.ReconnectRetryPolicy = new ExponentialRetry(100);

            redisConnectionOptions.KeepAlive = 180;
            hash_max_ziplist_entries = hash_max_ziplist_entries_;
            maxmemory_samples = maxmemory_samples_;
            maxmemory = maxmemory_;
        }

        public Task InitializeAsync()
        {
            EnsureRedisConnected();
            initInflux();
            AppDomain appd = AppDomain.CurrentDomain;
            appd.ProcessExit += (s, e) => {
                close_program();
            };
            Console.CancelKeyPress += (sender, e) => {
                close_program();
            };
            return Task.CompletedTask;
        }

        public void close_program(){
            writeApi0.Dispose();
            influxclient.Dispose();
            System.Console.WriteLine("close program.");
        }

        private void EnsureRedisConnected()
        {
            if (isRedisConnectionOpened)
            {
                return;
            }

            // Connection is closed or failed - open a new one but only at the first thread
            lock (locker)
            {
                if (isRedisConnectionOpened)
                {
                    return;
                }

                Console.WriteLine("Connecting to Redis: " + connectionString);
                redis = ConnectionMultiplexer.Connect(redisConnectionOptions);

                if (redis == null || !redis.IsConnected)
                {
                    Console.WriteLine("Wasn't able to connect to redis");

                    // We weren't able to connect to redis despite 5 retries with exponential backoff
                    throw new ApplicationException("Wasn't able to connect to redis");
                }

                Console.WriteLine("Successfully connected to Redis");

                var cache = redis.GetDatabase();

                Console.WriteLine("Performing small test");
                cache.StringSet("cart", "OK" );
                object res = cache.StringGet("cart");
                Console.WriteLine($"Small test result: {res}");

                Console.WriteLine("changing redis configuration...");
                Console.WriteLine("config set maxmemory response : " + cache.Execute("CONFIG", "SET", "maxmemory",maxmemory).ToString());
                Console.WriteLine("config set maxmemory-samples response : " + cache.Execute("CONFIG", "SET", "maxmemory-samples",maxmemory_samples).ToString());
                Console.WriteLine("config set hash-max-ziplist-entries response : " + cache.Execute("CONFIG", "SET", "hash-max-ziplist-entries",hash_max_ziplist_entries).ToString());

                redis.InternalError += (o, e) => { Console.WriteLine(e.Exception); };
                redis.ConnectionRestored += (o, e) =>
                {
                    isRedisConnectionOpened = true;
                    Console.WriteLine("Connection to redis was retored successfully");
                };
                redis.ConnectionFailed += (o, e) =>
                {
                    Console.WriteLine("Connection failed. Disposing the object");
                    isRedisConnectionOpened = false;
                };

                isRedisConnectionOpened = true;
            }
        }

        public async Task AddItemAsync(string userId, string productId, int quantity)
        {
            Console.WriteLine($"AddItemAsync called with userId={userId}, productId={productId}, quantity={quantity}");

            try
            {
                EnsureRedisConnected();

                var db = redis.GetDatabase();

                // Access the cart from the cache

                long  start = DateTime.Now.Ticks;
                var value = await db.HashGetAsync(userId, CART_FIELD_NAME);
                // get latency in microseconds
                long  latency = (DateTime.Now.Ticks - start)/10;
                var point = PointData.Measurement("service_metric")
                    .Field("latency", latency).Tag("op", "get").Tag("service", "cartservice");
                Console.WriteLine("hash get async latency "+latency.ToString());
                Write2Influx(point);
                
                Hipstershop.Cart cart;
                if (value.IsNull)
                {
                    cart = new Hipstershop.Cart();
                    cart.UserId = userId;
                    cart.Items.Add(new Hipstershop.CartItem { ProductId = productId, Quantity = quantity });
                }
                else
                {
                    cart = Hipstershop.Cart.Parser.ParseFrom(value);
                    var existingItem = cart.Items.SingleOrDefault(i => i.ProductId == productId);
                    if (existingItem == null)
                    {
                        cart.Items.Add(new Hipstershop.CartItem { ProductId = productId, Quantity = quantity });
                    }
                    else
                    {
                        existingItem.Quantity += quantity;
                    }
                }

                start = DateTime.Now.Ticks;
                await db.HashSetAsync(userId, new[]{ new HashEntry(CART_FIELD_NAME, cart.ToByteArray()) });
                // get latency in microseconds
                latency = (DateTime.Now.Ticks - start)/10;
            
                var point2 = PointData.Measurement("service_metric")
                    .Field("latency", latency).Tag("op", "set").Tag("service", "cartservice");
                Console.WriteLine("hash set async latency "+latency.ToString());
                Write2Influx(point2);
            }
            catch (Exception ex)
            {
                throw new RpcException(new Status(StatusCode.FailedPrecondition, $"Can't access cart storage. {ex}"));
            }
        }

        public async Task EmptyCartAsync(string userId)
        {
            Console.WriteLine($"EmptyCartAsync called with userId={userId}");

            try
            {
                EnsureRedisConnected();
                var db = redis.GetDatabase();

                // Update the cache with empty cart for given user
                long  start = DateTime.Now.Ticks;
                await db.HashSetAsync(userId, new[] { new HashEntry(CART_FIELD_NAME, emptyCartBytes) });
                // get latency in microseconds
                long  latency = (DateTime.Now.Ticks - start)/10;

                var point = PointData.Measurement("service_metric")
                    .Field("latency", latency).Tag("op", "set").Tag("service", "cartservice");
                Console.WriteLine("hash set async latency "+latency.ToString());
                Write2Influx(point);
                
            }
            catch (Exception ex)
            {
                throw new RpcException(new Status(StatusCode.FailedPrecondition, $"Can't access cart storage. {ex}"));
            }
        }

        public async Task<Hipstershop.Cart> GetCartAsync(string userId)
        {
            Console.WriteLine($"GetCartAsync called with userId={userId}");

            try
            {
                EnsureRedisConnected();

                var db = redis.GetDatabase();

                // Access the cart from the cache
                long  start = DateTime.Now.Ticks;
                var value = await db.HashGetAsync(userId, CART_FIELD_NAME);
                // get latency in microseconds
                long  latency = (DateTime.Now.Ticks - start)/10;
                var point = PointData.Measurement("service_metric")
                    .Field("latency", latency).Tag("op", "get").Tag("service", "cartservice");
                Console.WriteLine("hash get async latency "+latency.ToString());
                Write2Influx(point);

                if (!value.IsNull)
                {
                    return Hipstershop.Cart.Parser.ParseFrom(value);
                }

                // We decided to return empty cart in cases when user wasn't in the cache before
                return new Hipstershop.Cart();
            }
            catch (Exception ex)
            {
                throw new RpcException(new Status(StatusCode.FailedPrecondition, $"Can't access cart storage. {ex}"));
            }
        }

        public bool Ping()
        {
            try
            {
                var cache = redis.GetDatabase();
                var res = cache.Ping();
                return res != TimeSpan.Zero;
            }
            catch (Exception)
            {
                return false;
            }
        }
    }
}