"""
Hyperliquid Light Client

A minimal client for interacting with Hyperliquid's API with three core functionalities:
1. Retrieving price data (HTTP snapshots and WebSocket real-time)
2. Sending trades (market orders)
3. Querying portfolio balance and wallet information

Usage:
    client = HyperClient("ACCOUNT_ADDRESS", "API_SECRET")
    
    # Get price data
    btc_price = client.get_mid_price("BTC")
    
    # Send trade
    result = client.market_buy("BTC", 100)  # Buy $100 notional of BTC
    
    # Check balance
    equity = client.get_equity()
"""

import requests
import pandas as pd
import time
import json
import asyncio
import websockets
from typing import Dict, Optional, Any, List, Union, Callable
from eth_account import Account
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
import traceback

# Import the new handler functions
# Adjusted path for being inside api/ directory, model_handlers is a sibling
from ..model_handlers.model_stream_handler import simple_trade_data_handler, detailed_trade_data_handler
# Import for userFills
from ..data_handlers.fill_handler import user_fill_handler


class HyperClient:
    """
    A lightweight client for Hyperliquid trading platform.
    
    Provides basic functionality for price data, trading, and portfolio management.
    """
    
    def __init__(self, account_address: str, api_secret: str, testnet: bool = False):
        """
        Initialize the Hyperliquid client.
        
        Args:
            account_address: Your main wallet public key (0x...)
            api_secret: Your API wallet private key
            testnet: Whether to use testnet (default: False)
        """
        self.account_address = account_address
        self.api_secret = api_secret # Storing for potential re-use or audit, though wallet object is primary
        self.testnet = testnet
        
        # Set base URLs
        if testnet:
            self.base_url = "https://api.hyperliquid-testnet.xyz"
            self.ws_url = "wss://api.hyperliquid-testnet.xyz/ws"
        else:
            self.base_url = "https://api.hyperliquid.xyz"
            self.ws_url = "wss://api.hyperliquid.xyz/ws"
        
        # Initialize SDK components
        try:
            # Create wallet from private key
            wallet = Account.from_key(api_secret)
            
            self.exchange = Exchange(
                wallet=wallet,
                base_url=self.base_url, # SDK handles None for mainnet default
                account_address=account_address
            )
            # skip_ws=True for Info if not using its WebSocket features directly, 
            # as our client has its own ws stream_trades method.
            self.info = Info(base_url=self.base_url, skip_ws=True) 
        except Exception as e:
            raise Exception(f"Failed to initialize Hyperliquid client: {e}")
    
    # ============================================================================
    # 1. PRICE DATA RETRIEVAL
    # ============================================================================
    
    def get_all_mids(self) -> pd.Series:
        """
        Get snapshot of mid-prices for all trading pairs.
        
        Returns:
            pandas.Series: Mid-prices indexed by symbol with timestamp as name
        """
        try:
            body = {"type": "allMids"}
            response = requests.post(f"{self.base_url}/info", json=body, timeout=10)
            response.raise_for_status()
            
            return pd.Series(response.json(), name=time.time())
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch mid-prices: {e}")
    
    def get_mid_price(self, symbol: str) -> float:
        """
        Get current mid-price for a specific symbol.
        
        Args:
            symbol: Trading symbol (e.g., "BTC", "ETH")
            
        Returns:
            float: Current mid-price
        """
        try:
            mids = self.get_all_mids()
            if symbol not in mids.index: # Check if symbol exists in the Series index
                raise ValueError(f"Symbol {symbol} not found in available markets")
            
            return float(mids[symbol])
        except Exception as e: 
            raise Exception(f"Failed to fetch price for {symbol}: {e}")
    
    async def _manage_websocket_stream(self, subscription_details: dict, message_handler_callback: Callable, stream_description: str):
        """
        Private helper to manage a generic WebSocket stream lifecycle.

        Args:
            subscription_details (dict): The specific subscription payload (e.g., {"type": "trades", "coin": "BTC"}).
            message_handler_callback (Callable): A callback function that takes (parsed_message, stream_description) and processes it.
            stream_description (str): A descriptive name for the stream for logging (e.g., "TradesStream(BTC)").
        """
        print(f"[HyperClient._manage_websocket_stream] Attempting to connect to {stream_description} at {self.ws_url}")
        try:
            async with websockets.connect(self.ws_url) as websocket:
                full_subscribe_msg = {"method": "subscribe", "subscription": subscription_details}
                await websocket.send(json.dumps(full_subscribe_msg))
                print(f"[HyperClient._manage_websocket_stream] Subscribed to {stream_description}. Waiting for messages...")

                while True:
                    message = await websocket.recv()
                    raw_message_for_reporting = message # Keep a reference for detailed error reporting if needed
                    parsed_message = None
                    try:
                        if isinstance(message, str):
                            parsed_message = json.loads(message)
                        elif isinstance(message, bytes):
                            parsed_message = json.loads(message.decode('utf-8'))
                        else:
                            # Should ideally be JSON string or bytes, but pass as is if not handled by specific handler
                            parsed_message = message 
                        
                        # Pass to the specific message handler provided by the public stream method
                        message_handler_callback(parsed_message, stream_description, raw_message_for_reporting)

                    except json.JSONDecodeError as e_json:
                        print(f"[HyperClient._manage_websocket_stream] JSONDecodeError for {stream_description}: {e_json}. Raw message: {raw_message_for_reporting}")
                        # Optionally, notify handler of error: message_handler_callback({"error": "JSONDecodeError", ...}, ...)
                    except Exception as e_callback_or_parse: # Catch errors from within the message_handler_callback too
                        print(f"[HyperClient._manage_websocket_stream] Error in message_handler_callback for {stream_description}: {e_callback_or_parse}.")
                        traceback.print_exc()
                        # Optionally, notify handler of error
        
        except websockets.exceptions.ConnectionClosed as e_closed:
            print(f"[HyperClient._manage_websocket_stream] WebSocket connection for {stream_description} closed: Code {e_closed.code}, Reason: {e_closed.reason}")
            raise # Re-raise to allow calling method to handle (e.g., timeout, graceful exit)
        except websockets.exceptions.WebSocketException as e_ws:
            print(f"[HyperClient._manage_websocket_stream] WebSocketException for {stream_description}: {e_ws}")
            raise # Re-raise
        except Exception as e_general:
            print(f"[HyperClient._manage_websocket_stream] Unexpected error in {stream_description}: {e_general}")
            traceback.print_exc()
            raise # Re-raise

    async def stream_trades(self, symbol: str = "BTC", callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        """
        Stream real-time trades for a specific symbol via WebSocket.
        Passes a parsed dictionary or list (from JSON) to the callback.
        """
        final_trade_handler = callback if callback is not None else simple_trade_data_handler
        if callback is None:
            # This print is more for the user of HyperClient, not the generic stream manager
            print(f"[HyperClient.stream_trades] No custom callback provided, using default simple_trade_data_handler for {symbol}.")

        subscription_details = {"type": "trades", "coin": symbol}
        stream_description = f"TradesStream({symbol})"

        def internal_message_handler(parsed_message, stream_desc, raw_message):
            # The simple_trade_data_handler and detailed_trade_data_handler expect the full parsed_message
            # This wrapper maintains the original error handling specific to stream_trades if needed
            try:
                final_trade_handler(parsed_message)
            except Exception as e_callback:
                # This specific error logging was in the original stream_trades
                print(f"[HyperClient.stream_trades] Error in callback for {stream_desc}: {e_callback}. Raw message: {raw_message}")
                traceback.print_exc()
                # Optionally, if your handlers are designed to receive error dicts:
                # final_trade_handler({"error": "CallbackProcessingError", "details": str(e_callback), "raw_message": raw_message})

        await self._manage_websocket_stream(subscription_details, internal_message_handler, stream_description)

    async def stream_user_fills(self, callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        """
        Streams real-time user fill events for the authenticated user via WebSocket.
        Passes parsed fill data to the callback.
        """
        final_fill_handler = callback if callback is not None else user_fill_handler
        if callback is None:
            print(f"[HyperClient.stream_user_fills] No custom callback, using default user_fill_handler.")

        subscription_details = {"type": "userFills", "user": self.account_address}
        stream_description = "UserFillsStream"

        def internal_message_handler(parsed_message, stream_desc, raw_message):
            # This wrapper handles the specific structure of userFills messages
            # and SubscriptionResponse, then calls the final_fill_handler with the relevant part.
            try:
                if isinstance(parsed_message, dict) and parsed_message.get("channel") == "userFills" and "data" in parsed_message:
                    final_fill_handler(parsed_message["data"]) 
                elif isinstance(parsed_message, dict) and parsed_message.get("channel") == "subscriptionResponse":
                    print(f"[HyperClient.stream_user_fills] Subscription Response from {stream_desc}: {parsed_message}")
                else:
                    print(f"[HyperClient.stream_user_fills] Received unexpected message format on {stream_desc}: {parsed_message}")
            except Exception as e_callback:
                print(f"[HyperClient.stream_user_fills] Error in callback for {stream_desc}: {e_callback}. Raw message: {raw_message}")
                traceback.print_exc()
                # Optionally, if your handlers are designed to receive error dicts:
                # final_fill_handler({"error": "CallbackProcessingError", "details": str(e_callback), "raw_message": raw_message})
        
        await self._manage_websocket_stream(subscription_details, internal_message_handler, stream_description)
    
    # ============================================================================
    # 2. TRADING FUNCTIONALITY
    # ============================================================================
    
    def market_buy(self, symbol: str, asset_size: float) -> Dict[str, Any]:
        try:
            # The SDK's market_open sz parameter is in asset terms (e.g., 0.01 BTC)
            result = self.exchange.market_open(name=symbol, is_buy=True, sz=float(asset_size))
            return result
        except Exception as e:
            raise Exception(f"Failed to execute market buy for {symbol}: {e}")
    
    def market_sell(self, symbol: str, asset_size: float) -> Dict[str, Any]:
        try:
            # The SDK's market_open sz parameter is in asset terms
            result = self.exchange.market_open(name=symbol, is_buy=False, sz=float(asset_size))
            return result
        except Exception as e:
            raise Exception(f"Failed to execute market sell for {symbol}: {e}")
    
    def limit_order(self, symbol: str, is_buy: bool, size: float, price: float) -> Dict[str, Any]:
        try:
            result = self.exchange.order(name=symbol, is_buy=is_buy, sz=size, limit_px=price, order_type={"limit": {"tif": "Gtc"}})
            return result
        except Exception as e:
            order_type = "buy" if is_buy else "sell"
            raise Exception(f"Failed to place {order_type} limit order for {symbol}: {e}")
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """
        Cancels an open order.

        Args:
            symbol (str): The asset symbol of the order to cancel (e.g., "BTC").
            order_id (int): The ID of the order to cancel.

        Returns:
            Dict[str, Any]: The response from the cancel order API call.
        """
        try:
            # The SDK's cancel method expects the coin name and order ID
            print(f"[HyperClient] Attempting to cancel order ID {order_id} for symbol {symbol}")
            result = self.exchange.cancel(name=symbol, oid=order_id)
            print(f"[HyperClient] Cancel order response for {order_id}: {result}")
            return result
        except Exception as e:
            raise Exception(f"Failed to cancel order ID {order_id} for {symbol}: {e}")
    
    # ============================================================================
    # 3. PORTFOLIO & BALANCE QUERIES
    # ============================================================================
    
    def get_portfolio(self) -> Dict[str, Any]:
        try:
            user_state = self.info.user_state(self.account_address)
            return user_state
        except Exception as e:
            raise Exception(f"Failed to fetch portfolio data (user_state): {e}")
    
    def get_equity(self) -> float:
        try:
            user_state = self.info.user_state(self.account_address)
            if user_state:
                if "crossMarginSummary" in user_state and isinstance(user_state["crossMarginSummary"], dict):
                    return float(user_state["crossMarginSummary"].get("accountValue", 0.0))
                if "marginSummary" in user_state and isinstance(user_state["marginSummary"], dict): 
                    return float(user_state["marginSummary"].get("accountValue", 0.0))
                if "accountValue" in user_state:
                     return float(user_state["accountValue"])
            return 0.0
        except Exception as e:
            raise Exception(f"Failed to fetch or parse equity from user_state: {e}")
    
    def get_margin_summary(self) -> Dict[str, Any]:
        try:
            user_state = self.info.user_state(self.account_address)
            if user_state:
                if "crossMarginSummary" in user_state and isinstance(user_state["crossMarginSummary"], dict):
                    return user_state["crossMarginSummary"]
                if "marginSummary" in user_state and isinstance(user_state["marginSummary"], dict): 
                    return user_state["marginSummary"]
            return {}
        except Exception as e:
            raise Exception(f"Failed to fetch margin summary from user_state: {e}")
    
    def get_positions(self) -> List[Dict[str, Any]]:
        try:
            user_state = self.info.user_state(self.account_address)
            if user_state and "assetPositions" in user_state and isinstance(user_state["assetPositions"], list):
                return user_state["assetPositions"]
            return []
        except Exception as e:
            raise Exception(f"Failed to fetch positions from user_state: {e}")
    
    def get_balance(self) -> Dict[str, float]:
        try:
            response = requests.post(
                f"{self.base_url}/info",
                json={"type": "spotClearinghouseState", "user": self.account_address},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            if "balances" in data and isinstance(data["balances"], list):
                return {balance.get("coin", "UNKNOWN"): float(balance.get("total", 0.0)) for balance in data["balances"]}
            return {}
        except Exception as e:
            raise Exception(f"Failed to fetch spot balances: {e}")
    
    def get_l2_book(self, symbol: str, n_sig_figs: Optional[int] = None) -> Dict[str, Any]:
        """
        Get L2 order book snapshot for a specific symbol.
        
        Args:
            symbol: Trading symbol (e.g., "BTC", "ETH")
            n_sig_figs: Optional number of significant figures for price aggregation (2-5)
            
        Returns:
            dict: Order book with bids and asks
        """
        try:
            body = {
                "type": "l2Book",
                "coin": symbol
            }
            if n_sig_figs is not None and n_sig_figs in [2, 3, 4, 5]:
                body["nSigFigs"] = n_sig_figs
                
            response = requests.post(f"{self.base_url}/info", json=body, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Handle the actual response format from Hyperliquid
            if isinstance(data, dict) and "levels" in data:
                levels = data["levels"]
                if isinstance(levels, list) and len(levels) == 2:
                    return {
                        "bids": levels[0],  # List of {"px": price, "sz": size, "n": num_orders}
                        "asks": levels[1]   # List of {"px": price, "sz": size, "n": num_orders}
                    }
            # Handle the old format just in case
            elif isinstance(data, list) and len(data) == 2:
                return {
                    "bids": data[0],
                    "asks": data[1]
                }
            return {"bids": [], "asks": []}
        except Exception as e:
            raise Exception(f"Failed to fetch L2 book for {symbol}: {e}")
    
    def get_best_bid_ask(self, symbol: str) -> Dict[str, Optional[float]]:
        """
        Get best bid and ask prices for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., "BTC", "ETH")
            
        Returns:
            dict: {"bid": best_bid_price, "ask": best_ask_price, "spread": spread}
        """
        try:
            book = self.get_l2_book(symbol)
            
            best_bid = None
            best_ask = None
            
            if book["bids"] and len(book["bids"]) > 0:
                best_bid = float(book["bids"][0]["px"])
                
            if book["asks"] and len(book["asks"]) > 0:
                best_ask = float(book["asks"][0]["px"])
                
            spread = None
            if best_bid is not None and best_ask is not None:
                spread = best_ask - best_bid
                
            return {
                "bid": best_bid,
                "ask": best_ask,
                "spread": spread,
                "spread_percentage": (spread / best_bid * 100) if best_bid and spread else None
            }
        except Exception as e:
            raise Exception(f"Failed to get best bid/ask for {symbol}: {e}")
    
    def get_24h_stats(self, symbol: str) -> Dict[str, Any]:
        """
        Get 24-hour statistics for a symbol using candle data.
        
        Args:
            symbol: Trading symbol (e.g., "BTC", "ETH")
            
        Returns:
            dict: 24h stats including high, low, volume, price change
        """
        try:
            # Get 24h candle data
            end_time = int(time.time() * 1000)
            start_time = end_time - (24 * 60 * 60 * 1000)  # 24 hours ago
            
            body = {
                "type": "candleSnapshot",
                "req": {
                    "coin": symbol,
                    "interval": "1h",
                    "startTime": start_time,
                    "endTime": end_time
                }
            }
            
            response = requests.post(f"{self.base_url}/info", json=body, timeout=10)
            response.raise_for_status()
            
            candles = response.json()
            
            if not candles or not isinstance(candles, list):
                return {}
                
            # Calculate 24h stats from hourly candles
            high_24h = max(float(c["h"]) for c in candles)
            low_24h = min(float(c["l"]) for c in candles)
            volume_24h = sum(float(c["v"]) for c in candles)
            
            # Get price 24h ago and current price
            price_24h_ago = float(candles[0]["o"])  # Open of first candle
            current_price = float(candles[-1]["c"])  # Close of last candle
            
            price_change = current_price - price_24h_ago
            price_change_percent = (price_change / price_24h_ago * 100) if price_24h_ago else 0
            
            return {
                "high_24h": high_24h,
                "low_24h": low_24h,
                "volume_24h": volume_24h,
                "price_24h_ago": price_24h_ago,
                "current_price": current_price,
                "price_change": price_change,
                "price_change_percent": price_change_percent
            }
        except Exception as e:
            raise Exception(f"Failed to get 24h stats for {symbol}: {e}")
    
    def get_full_market_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive market data including price, bid/ask, and 24h stats.
        
        Args:
            symbol: Trading symbol (e.g., "BTC", "ETH")
            
        Returns:
            dict: Complete market data
        """
        try:
            # Get mid price
            mid_price = self.get_mid_price(symbol)
            
            # Get bid/ask data
            bid_ask = self.get_best_bid_ask(symbol)
            
            # Get 24h stats
            stats_24h = self.get_24h_stats(symbol)
            
            return {
                "symbol": symbol,
                "mid_price": mid_price,
                "bid": bid_ask.get("bid"),
                "ask": bid_ask.get("ask"),
                "spread": bid_ask.get("spread"),
                "spread_percentage": bid_ask.get("spread_percentage"),
                "high_24h": stats_24h.get("high_24h"),
                "low_24h": stats_24h.get("low_24h"),
                "volume_24h": stats_24h.get("volume_24h"),
                "price_24h_ago": stats_24h.get("price_24h_ago"),
                "price_change": stats_24h.get("price_change"),
                "price_change_percent": stats_24h.get("price_change_percent"),
                "timestamp": int(time.time() * 1000)
            }
        except Exception as e:
            raise Exception(f"Failed to get full market data for {symbol}: {e}")
    
    def get_user_fills_by_time(self, start_time: int, end_time: Optional[int] = None, aggregate_by_time: bool = False) -> List[Dict[str, Any]]:
        """
        Get user fills within a time range.
        
        Args:
            start_time: Start time in milliseconds (inclusive)
            end_time: End time in milliseconds (inclusive). Defaults to current time.
            aggregate_by_time: When true, partial fills are combined
            
        Returns:
            List of fill dictionaries containing trade information
        """
        try:
            body = {
                "type": "userFillsByTime",
                "user": self.account_address,
                "startTime": start_time
            }
            
            if end_time is not None:
                body["endTime"] = end_time
            else:
                body["endTime"] = int(time.time() * 1000)
                
            if aggregate_by_time:
                body["aggregateByTime"] = True
                
            response = requests.post(f"{self.base_url}/info", json=body, timeout=10)
            response.raise_for_status()
            
            fills = response.json()
            
            # Return empty list if no fills
            if not fills or not isinstance(fills, list):
                return []
                
            return fills
            
        except Exception as e:
            raise Exception(f"Failed to fetch user fills: {e}")
    
    def get_user_fills(self, aggregate_by_time: bool = False) -> List[Dict[str, Any]]:
        """
        Get recent user fills (up to 2000 most recent).
        
        Args:
            aggregate_by_time: When true, partial fills are combined
            
        Returns:
            List of fill dictionaries containing trade information
        """
        try:
            body = {
                "type": "userFills",
                "user": self.account_address
            }
            
            if aggregate_by_time:
                body["aggregateByTime"] = True
                
            response = requests.post(f"{self.base_url}/info", json=body, timeout=10)
            response.raise_for_status()
            
            fills = response.json()
            
            # Return empty list if no fills
            if not fills or not isinstance(fills, list):
                return []
                
            return fills
            
        except Exception as e:
            raise Exception(f"Failed to fetch user fills: {e}")
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def get_exchange_info(self) -> Dict[str, Any]:
        try:
            meta = self.info.meta()
            return meta
        except Exception as e:
            raise Exception(f"Failed to fetch exchange info (meta): {e}")
    
    def health_check(self) -> bool:
        try:
            self.get_all_mids()
            return True
        except Exception:
            return False