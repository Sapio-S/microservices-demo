using System;
using System.Linq;
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

        private static readonly char[] Token = "nMbCj1HHoEV5UTcZBBrtm6kkQ4xzlK8I0EfRrZO2i6ngr3mBB4y0XLUQvBdxTZCnHDoHZQgaNRGbhfSZ9A76fQ==".ToCharArray();
        private static List<InfluxDB.Client.Writes.PointData> points  = new List<InfluxDB.Client.Writes.PointData>();
        // private static List<string> measurement = new List<string>();
        private static int cnt = 0;

        private readonly ConfigurationOptions redisConnectionOptions;

        public void Write2Influx(){
            if(cnt < 10){
                return;
            }
            var influxDBClient = InfluxDBClientFactory.Create("http://localhost:8086", Token);

            using (var writeApi = influxDBClient.GetWriteApi())
            {
                // writeApi.WritePoint("trace", "MSRA", points);
                for (int i = 0; i < cnt; i++){
                    writeApi.WritePoint("trace", "MSRA", points[i]);
                }
            }
            influxDBClient.Dispose();
            cnt = 0;
            points.Clear();
        }

        public RedisCartStore(string redisAddress)
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

        }

        public Task InitializeAsync()
        {
            EnsureRedisConnected();
            return Task.CompletedTask;
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
                var point = PointData.Measurement("hash get async")
                    .Field("latency", latency)
                    .Timestamp(DateTime.UtcNow.AddSeconds(-10), WritePrecision.Ns);
                points.Add(point);
                Console.WriteLine("hash get async latency "+latency.ToString());
                cnt += 1;
                // Write2Influx();
                
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
            
                var point2 = PointData.Measurement("hash set async")
                    .Field("latency", latency)
                    .Timestamp(DateTime.UtcNow.AddSeconds(-10), WritePrecision.Ns);
                points.Add(point2);
                Console.WriteLine("hash set async latency "+latency.ToString());
                cnt += 1;
                // Write2Influx();
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

                var point = PointData.Measurement("hash set async")
                    .Field("latency", latency)
                    .Timestamp(DateTime.UtcNow.AddSeconds(-10), WritePrecision.Ns);
                points.Add(point);
                Console.WriteLine("hash set async latency "+latency.ToString());
                cnt += 1;
                // Write2Influx();
                
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
                var point = PointData.Measurement("hash get async")
                    .Field("latency", latency)
                    .Timestamp(DateTime.UtcNow.AddSeconds(-10), WritePrecision.Ns);
                points.Add(point);
                Console.WriteLine("hash get async latency "+latency.ToString());
                cnt += 1;
                // Write2Influx();

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