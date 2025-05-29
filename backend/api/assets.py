from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import sys
import os
import time

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.hyperliquid_wrapper.api.hyperliquid_client import HyperClient
from hyperliquid.info import Info
from hyperliquid.utils import constants
from backend.api.models import PriceData, CurrentPrice, AssetInfo, LivePriceData, UserTrade
from src.config import config

router = APIRouter()

# Initialize client using config
try:
    client = HyperClient(**config.get_hyperliquid_client_params())
    print(f"[Assets API] Initialized HyperClient for {config.network_name}")
    
    # Also initialize Info directly for candles
    info = Info(constants.MAINNET_API_URL if config.is_mainnet else constants.TESTNET_API_URL, skip_ws=True)
    client_initialized = True
except Exception as e:
    print(f"[Assets API] WARNING: Failed to initialize HyperClient: {e}")
    print(f"[Assets API] The API will start but asset endpoints may not work until the Hyperliquid API is available")
    client = None
    info = None
    client_initialized = False

def ensure_client():
    """Ensure the client is initialized before using it."""
    global client, info, client_initialized
    
    if not client_initialized:
        try:
            client = HyperClient(**config.get_hyperliquid_client_params())
            info = Info(constants.MAINNET_API_URL if config.is_mainnet else constants.TESTNET_API_URL, skip_ws=True)
            client_initialized = True
            print(f"[Assets API] Successfully initialized HyperClient for {config.network_name}")
        except Exception as e:
            raise HTTPException(
                status_code=503, 
                detail=f"Hyperliquid API is currently unavailable: {str(e)}. Please try again later."
            )
    
    return client, info

@router.get("/assets/{symbol}/price-history")
async def get_price_history(symbol: str, days: int = 180, quote: str = "USD", interval: Optional[str] = None):
    """
    Get price history for an asset using Hyperliquid's candle data.
    
    Args:
        symbol: Asset symbol (e.g., "BTC", "ETH")
        days: Number of days of history to return (default: 180 for 6 months)
        quote: Quote asset (default: "USD"). Note: Hyperliquid primarily supports USD pairs.
        interval: Candle interval (optional: "5m", "1h", "1d"). If not provided, auto-selects based on days.
    """
    try:
        # Ensure client is initialized
        _, info = ensure_client()
        
        # Special handling for known invalid symbols
        if symbol.upper() == "HYP":
            raise HTTPException(
                status_code=404, 
                detail=f"Symbol '{symbol}' not found. Note: Hyperliquid does not trade its own token (HYP) on the platform. Try BTC, ETH, SOL, or other supported assets."
            )
        
        # For now, Hyperliquid primarily supports USD pairs
        # If a non-USD quote is requested, we'll need to handle conversion
        if quote.upper() != "USD":
            # Log the request for non-USD quote
            print(f"Warning: Non-USD quote requested: {symbol}/{quote}. Hyperliquid primarily supports USD pairs.")
            # For now, we'll still fetch USD data but note the limitation
            # In the future, this could be extended to support synthetic pairs
        
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # Convert to milliseconds
        start_time_ms = int(start_time.timestamp() * 1000)
        end_time_ms = int(end_time.timestamp() * 1000)
        
        # Determine interval - use provided interval or auto-select based on days
        if interval:
            # Map frontend intervals to Hyperliquid intervals
            interval_map = {
                "5m": "5m",
                "1h": "1h", 
                "1d": "1d"
            }
            candle_interval = interval_map.get(interval, interval)
        else:
            # Auto-select interval based on days requested
            if days <= 7:
                candle_interval = "1h"  # Hourly for up to 7 days
            elif days <= 30:
                candle_interval = "4h"  # 4-hour candles for up to 30 days
            else:
                candle_interval = "1d"  # Daily candles for longer periods
        
        # Fetch candle data from Hyperliquid using the info.post method
        request_body = {
            "type": "candleSnapshot",
            "req": {
                "coin": symbol,
                "interval": candle_interval,
                "startTime": start_time_ms,
                "endTime": end_time_ms
            }
        }
        
        print(f"Requesting candle data for {symbol} with interval {candle_interval}")
        # The post method expects (url_path, json_body)
        candle_data = info.post("/info", request_body)
        print(f"Received candle data: {type(candle_data)}, length: {len(candle_data) if candle_data else 0}")
        
        # Transform candle data to our format
        price_history = []
        
        if candle_data and isinstance(candle_data, list):
            for candle in candle_data:
                # Candle format from Hyperliquid:
                # {
                #   "t": open_time_ms,
                #   "T": close_time_ms,
                #   "s": symbol,
                #   "i": interval,
                #   "o": open_price,
                #   "c": close_price,
                #   "h": high_price,
                #   "l": low_price,
                #   "v": volume,
                #   "n": number_of_trades
                # }
                
                # Convert timestamp to date
                timestamp_ms = candle.get("t", 0)
                if timestamp_ms:
                    date = datetime.fromtimestamp(timestamp_ms / 1000)
                    
                    price_history.append({
                        "date": date.strftime("%Y-%m-%d"),
                        "timestamp": timestamp_ms,
                        "price": float(candle.get("c", 0)),  # Using close price as the main price
                        "open": float(candle.get("o", 0)),
                        "high": float(candle.get("h", 0)),
                        "low": float(candle.get("l", 0)),
                        "close": float(candle.get("c", 0)),
                        "volume": float(candle.get("v", 0))  # Volume is already in asset terms
                    })
        
        # If we're using hourly or 4-hour data but want daily representation,
        # we might want to aggregate. For now, we'll return as-is.
        
        return {
            "symbol": symbol,
            "quote": quote,
            "days": days,
            "interval": candle_interval,
            "data": price_history,
            "count": len(price_history)
        }
        
    except Exception as e:
        error_msg = f"Error fetching price history for {symbol}: {str(e)}"
        print(error_msg)
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/assets/{symbol}/current")
async def get_current_price(symbol: str, quote: str = "USD"):
    """
    Get current price and market data for an asset including bid/ask spread and 24h stats
    
    Args:
        symbol: Asset symbol (e.g., "BTC", "ETH")
        quote: Quote asset (default: "USD"). Note: Hyperliquid primarily supports USD pairs.
    """
    try:
        # Special handling for known invalid symbols
        if symbol.upper() == "HYP":
            raise HTTPException(
                status_code=404, 
                detail=f"Symbol '{symbol}' not found. Note: Hyperliquid does not trade its own token (HYP) on the platform. Try BTC, ETH, SOL, or other supported assets."
            )
        
        # For now, Hyperliquid primarily supports USD pairs
        if quote.upper() != "USD":
            print(f"Warning: Non-USD quote requested: {symbol}/{quote}. Hyperliquid primarily supports USD pairs.")
        
        # Get comprehensive market data from Hyperliquid
        market_data = client.get_full_market_data(symbol)
        
        # If we couldn't get full data, fall back to just mid price
        if not market_data.get("mid_price"):
            price = client.get_mid_price(symbol)
            return {
                "symbol": symbol,
                "quote": quote,
                "price": price,
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
        
        return {
            "symbol": market_data["symbol"],
            "quote": quote,
            "price": market_data["mid_price"],
            "bid": market_data.get("bid"),
            "ask": market_data.get("ask"),
            "spread": market_data.get("spread"),
            "spread_percentage": market_data.get("spread_percentage"),
            "high_24h": market_data.get("high_24h"),
            "low_24h": market_data.get("low_24h"),
            "volume_24h": market_data.get("volume_24h"),
            "price_24h_ago": market_data.get("price_24h_ago"),
            "price_change": market_data.get("price_change"),
            "price_change_percent": market_data.get("price_change_percent"),
            "timestamp": market_data["timestamp"]
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        # Symbol not found
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found. Please check the symbol and try again.")
    except Exception as e:
        print(f"Error fetching current price for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get market data for {symbol}: {str(e)}")

@router.get("/assets/available")
async def get_available_assets():
    """
    Get list of available trading assets from Hyperliquid
    """
    try:
        # Get all mid prices to see available assets
        all_mids = client.get_all_mids()
        
        # Extract symbols and their current prices
        assets = []
        for symbol, price in all_mids.items():
            assets.append({
                "symbol": symbol,
                "price": float(price)
            })
        
        # Sort by symbol
        assets.sort(key=lambda x: x["symbol"])
        
        return {
            "assets": assets,
            "count": len(assets)
        }
        
    except Exception as e:
        print(f"Error fetching available assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/assets/{symbol}/live-data")
async def get_live_price_data(symbol: str, minutes: int = 30, quote: str = "USD"):
    """
    Get live price data for an asset with minute-level granularity.
    
    Args:
        symbol: Asset symbol (e.g., "BTC", "ETH")
        minutes: Number of minutes of history to return (default: 30)
        quote: Quote asset (default: "USD"). Note: Hyperliquid primarily supports USD pairs.
    """
    try:
        # Special handling for known invalid symbols
        if symbol.upper() == "HYP":
            raise HTTPException(
                status_code=404, 
                detail=f"Symbol '{symbol}' not found. Note: Hyperliquid does not trade its own token (HYP) on the platform. Try BTC, ETH, SOL, or other supported assets."
            )
        
        # For now, Hyperliquid primarily supports USD pairs
        if quote.upper() != "USD":
            print(f"Warning: Non-USD quote requested: {symbol}/{quote}. Hyperliquid primarily supports USD pairs.")
        
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=minutes)
        
        # Convert to milliseconds
        start_time_ms = int(start_time.timestamp() * 1000)
        end_time_ms = int(end_time.timestamp() * 1000)
        
        # Use 1-minute interval for live data
        interval = "1m"
        
        # Fetch candle data from Hyperliquid
        request_body = {
            "type": "candleSnapshot",
            "req": {
                "coin": symbol,
                "interval": interval,
                "startTime": start_time_ms,
                "endTime": end_time_ms
            }
        }
        
        print(f"Requesting live data for {symbol} with interval {interval} for {minutes} minutes")
        candle_data = info.post("/info", request_body)
        print(f"Received live data: {type(candle_data)}, length: {len(candle_data) if candle_data else 0}")
        
        # Transform candle data to our format
        price_data = []
        
        if candle_data and isinstance(candle_data, list):
            for candle in candle_data:
                timestamp_ms = candle.get("t", 0)
                if timestamp_ms:
                    price_data.append({
                        "timestamp": timestamp_ms,
                        "time": datetime.fromtimestamp(timestamp_ms / 1000).strftime("%H:%M:%S"),
                        "price": float(candle.get("c", 0)),
                        "open": float(candle.get("o", 0)),
                        "high": float(candle.get("h", 0)),
                        "low": float(candle.get("l", 0)),
                        "close": float(candle.get("c", 0)),
                        "volume": float(candle.get("v", 0))
                    })
        
        # Sort by timestamp to ensure chronological order
        price_data.sort(key=lambda x: x["timestamp"])
        
        return {
            "symbol": symbol,
            "quote": quote,
            "minutes": minutes,
            "interval": interval,
            "data": price_data,
            "count": len(price_data),
            "start_time": start_time_ms,
            "end_time": end_time_ms
        }
        
    except Exception as e:
        error_msg = f"Error fetching live data for {symbol}: {str(e)}"
        print(error_msg)
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/assets/{symbol}/user-trades")
async def get_user_trades(symbol: str, days: int = 180, quote: str = "USD"):
    """
    Get user's trades for a specific asset.
    
    Args:
        symbol: Asset symbol (e.g., "BTC", "ETH")
        days: Number of days of history to return (default: 180 for 6 months)
        quote: Quote asset (default: "USD"). Note: Hyperliquid primarily supports USD pairs.
    """
    try:
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # Convert to milliseconds
        start_time_ms = int(start_time.timestamp() * 1000)
        end_time_ms = int(end_time.timestamp() * 1000)
        
        # Get user fills for the time range
        fills = client.get_user_fills_by_time(start_time_ms, end_time_ms, aggregate_by_time=True)
        
        # Filter fills for the specific symbol
        symbol_fills = []
        for fill in fills:
            # Check if the fill is for the requested symbol
            fill_coin = fill.get("coin", "")
            
            # Handle both perpetual (e.g., "BTC") and spot (e.g., "@107") formats
            if fill_coin == symbol or (fill_coin.startswith("@") and quote != "USD"):
                # Transform fill data to our format
                symbol_fills.append({
                    "timestamp": fill.get("time", 0),
                    "date": datetime.fromtimestamp(fill.get("time", 0) / 1000).strftime("%Y-%m-%d %H:%M:%S"),
                    "price": float(fill.get("px", 0)),
                    "size": float(fill.get("sz", 0)),
                    "side": fill.get("side", ""),  # "B" for buy, "A" for sell (ask)
                    "direction": fill.get("dir", ""),  # "Open Long", "Close Short", etc.
                    "fee": float(fill.get("fee", 0)),
                    "pnl": float(fill.get("closedPnl", 0)),
                    "order_id": fill.get("oid", 0),
                    "trade_id": fill.get("tid", 0)
                })
        
        # Sort by timestamp
        symbol_fills.sort(key=lambda x: x["timestamp"])
        
        return {
            "symbol": symbol,
            "quote": quote,
            "days": days,
            "trades": symbol_fills,
            "count": len(symbol_fills)
        }
        
    except Exception as e:
        error_msg = f"Error fetching user trades for {symbol}: {str(e)}"
        print(error_msg)
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg) 