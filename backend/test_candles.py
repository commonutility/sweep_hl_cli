from hyperliquid.info import Info
from hyperliquid.utils import constants
from datetime import datetime, timedelta

# Initialize Info
info = Info(constants.MAINNET_API_URL, skip_ws=True)

# Test candles
end_time = datetime.now()
start_time = end_time - timedelta(days=7)

start_time_ms = int(start_time.timestamp() * 1000)
end_time_ms = int(end_time.timestamp() * 1000)

request_body = {
    "type": "candleSnapshot",
    "req": {
        "coin": "BTC",
        "interval": "1h",
        "startTime": start_time_ms,
        "endTime": end_time_ms
    }
}

print(f"Request body: {request_body}")

try:
    # The post method expects (url_path, json_body)
    result = info.post("/info", request_body)
    print(f"Result type: {type(result)}")
    if isinstance(result, list) and len(result) > 0:
        print(f"Number of candles: {len(result)}")
        print(f"First candle: {result[0]}")
        print(f"Last candle: {result[-1]}")
    else:
        print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")
    print(f"Error type: {type(e)}")
    import traceback
    traceback.print_exc() 