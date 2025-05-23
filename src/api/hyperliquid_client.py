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
    
    async def stream_trades(self, symbol: str = "BTC", callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        """
        Stream real-time trades for a specific symbol via WebSocket.
        Passes a parsed dictionary or list (from JSON) to the callback.
        """
        active_callback = callback if callback is not None else simple_trade_data_handler
        if callback is None:
            print(f"[HyperClient.stream_trades] No custom callback provided, using default simple_trade_data_handler for {symbol}.")

        try:
            async with websockets.connect(self.ws_url) as websocket:
                subscribe_msg = {"method": "subscribe", "subscription": {"type": "trades", "coin": symbol}}
                await websocket.send(json.dumps(subscribe_msg))
                print(f"[HyperClient.stream_trades] Subscribed to {symbol} trades. Waiting for messages...")

                while True:
                    message = await websocket.recv()
                    raw_message_for_error_reporting = message # Keep a copy
                    parsed_message = None

                    try:
                        if isinstance(message, str):
                            parsed_message = json.loads(message)
                        elif isinstance(message, bytes):
                            parsed_message = json.loads(message.decode('utf-8'))
                        else:
                            parsed_message = message 
                        
                        active_callback(parsed_message)

                    except json.JSONDecodeError as e_json:
                        print(f"[HyperClient.stream_trades] JSONDecodeError for {symbol}: {e_json}. Raw message: {raw_message_for_error_reporting}")
                        active_callback({"error": "JSONDecodeError", "details": str(e_json), "raw_message": raw_message_for_error_reporting})
                    except Exception as e_callback_or_parse:
                        print(f"[HyperClient.stream_trades] Error processing message or in callback for {symbol}: {e_callback_or_parse}.")
                        traceback.print_exc()
                        active_callback({"error": "CallbackProcessingError", "details": str(e_callback_or_parse), "raw_message": raw_message_for_error_reporting})

        except websockets.exceptions.ConnectionClosed as e_closed:
            print(f"[HyperClient.stream_trades] WebSocket connection for {symbol} closed: Code {e_closed.code}, Reason: {e_closed.reason}")
            raise 
        except websockets.exceptions.WebSocketException as e_ws:
            print(f"[HyperClient.stream_trades] WebSocketException for {symbol}: {e_ws}")
            raise
        except Exception as e_general:
            print(f"[HyperClient.stream_trades] Unexpected error in stream_trades for {symbol}: {e_general}")
            traceback.print_exc()
            raise
    
    # ============================================================================
    # 2. TRADING FUNCTIONALITY
    # ============================================================================
    
    def market_buy(self, symbol: str, notional_size: float) -> Dict[str, Any]:
        try:
            result = self.exchange.market_open(name=symbol, is_buy=True, sz=float(notional_size))
            return result
        except Exception as e:
            raise Exception(f"Failed to execute market buy for {symbol}: {e}")
    
    def market_sell(self, symbol: str, notional_size: float) -> Dict[str, Any]:
        try:
            result = self.exchange.market_open(name=symbol, is_buy=False, sz=float(notional_size))
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


# ============================================================================
# EXAMPLE ASYNC FUNCTION FOR WEBSOCKET DEMO (can be called from other scripts)
# ============================================================================

async def demo_streaming(client: HyperClient, symbol: str = "BTC", duration: int = 30):
    """
    Demo function to stream trades for a limited time using the detailed_trade_data_handler.
    This function can be imported and used by other scripts.
    """
    print(f"[hyperliquid_client.demo_streaming] Starting trade stream for {symbol} (duration: {duration}s).")
    print(f"                                Using callback: {detailed_trade_data_handler.__name__}")
    
    try:
        await asyncio.wait_for(
            client.stream_trades(symbol, detailed_trade_data_handler), # Pass the specific handler
            timeout=duration
        )
    except asyncio.TimeoutError:
        print(f"[hyperliquid_client.demo_streaming] Trade streaming for {symbol} ended after {duration} seconds (timeout).")
    except Exception as e:
        print(f"[hyperliquid_client.demo_streaming] Error during demo_streaming for {symbol}: {e}")
        traceback.print_exc()

# No if __name__ == "__main__": block for direct execution
# This file is intended to be a library. 