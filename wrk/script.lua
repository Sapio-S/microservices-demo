require "socket"
math.randomseed(socket.gettime()*1000)
math.random(); math.random(); math.random()

products = {
  '0PUK6V6EV0',
  '1YMWWN1N4O',
  '2ZYFJ3GM2N',
  '66VCHSJNUP',
  '6E92ZMYYFZ',
  '9SIQT8TOJO',
  'L9ECAV7KIM',
  'LS4PSXUNUM',
  'OLJCESPC7Z'
}

currencies = {'EUR', 'USD', 'JPY', 'CAD'}

local function index()
  local method = "GET"
  local path = "http://localhost:8080/"
  local headers = {}
  return wrk.format(method, path, headers, nil)
end

local function setCurrency()
  local id = math.random(4)
  local cur = currencies[id+1]
  local method = "POST"
  local path = "http://localhost:8080/setCurrency?currency_code=" .. cur
  local headers = {}
  return wrk.format(method, path, headers, nil)
end

local function browseProduct()
  local id = math.random(9)
  local pro = products[id+1]
  local method = "GET"
  local path = "http://localhost:8080/product/" .. pro
  local headers = {}
  return wrk.format(method, path, headers, nil)
end

local function viewCart()
  local method = "GET"
  local path = "http://localhost:8080/cart"
  local headers = {}
  return wrk.format(method, path, headers, nil)
end

local function checkout()
  local id = math.random(9)
  local pro = products[id+1]
  local r = {}
  local method1 = "GET"
  local path1 = "http://localhost:8080/product/" .. pro
  local headers = {}
  r[1] = wrk.format(method1, path1, headers, nil)
  local method2 = "POST"
  local num = math.random(10)
  -- need check
  local path2 = "http://localhost:8080/setCurrency?product_id=" .. pro .. "&quantity=" .. num
  r[2] = wrk.format(method2, path2, headers, nil)
  local method3 = "POST"
  local path3 = "http://localhost:8080/cart/checkout?email=someone@example.com&street_address=1600_Amphitheatre_Parkway&zip_code=94043&city=Mountain View&state=CA&country=United States&credit_card_number=4432-8015-6152-0454&credit_card_expiration_month=1&credit_card_expiration_year=2039&credit_card_cvv=672"
  r[3] = wrk.format(method3, path3, headers, nil)
  req = table.concat(r)
end

request = function()
  cur_time = math.floor(socket.gettime())
  local index_ratio      = 0.5
  local setCurrency_ratio   = 0.39
  local browseProduct_ratio        = 0.005
  local viewCart_ratio     = 0.005

  local coin = math.random()
  if coin < index_ratio then
    return index()
  elseif coin < index_ratio + setCurrency_ratio then
    return setCurrency()
  elseif coin < index_ratio + setCurrency_ratio + browseProduct_ratio then
    return browseProduct()
  else if coin < index_ratio + setCurrency_ratio + browseProduct_ratio + viewCart_ratio then
    return viewCart()
  else
    return 
  end
end