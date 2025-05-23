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
from model_handlers.model_stream_handler import simple_trade_data_handler, detailed_trade_data_handler


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
        self.api_secret = api_secret
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
                base_url=self.base_url if testnet else None,
                account_address=account_address
            )
            self.info = Info(base_url=self.base_url if testnet else None)
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
            body = {"type": "allMids"}
            response = requests.post(f"{self.base_url}/info", json=body, timeout=10)
            response.raise_for_status()
            
            mids = response.json()
            if symbol not in mids:
                raise ValueError(f"Symbol {symbol} not found in available markets")
            
            return float(mids[symbol])
        except requests.exceptions.RequestException as e:
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
                            # If it's already a dict/list (though websockets usually gives str/bytes)
                            parsed_message = message 
                        
                        active_callback(parsed_message)

                    except json.JSONDecodeError as e_json:
                        print(f"[HyperClient.stream_trades] JSONDecodeError for {symbol}: {e_json}. Raw message: {raw_message_for_error_reporting}")
                        # Optionally pass an error structure to the callback
                        active_callback({"error": "JSONDecodeError", "details": str(e_json), "raw_message": raw_message_for_error_reporting})
                    except Exception as e_callback_or_parse:
                        print(f"[HyperClient.stream_trades] Error processing message or in callback for {symbol}: {e_callback_or_parse}.")
                        traceback.print_exc()
                        active_callback({"error": "CallbackProcessingError", "details": str(e_callback_or_parse), "raw_message": raw_message_for_error_reporting})

        except websockets.exceptions.ConnectionClosed as e_closed:
            print(f"[HyperClient.stream_trades] WebSocket connection for {symbol} closed: Code {e_closed.code}, Reason: {e_closed.reason}")
            # Re-raise or handle as appropriate (e.g., attempt reconnect)
            raise # Or some custom exception
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
        """
        Execute a market buy order.
        
        Args:
            symbol: Trading symbol (e.g., "BTC", "ETH")
            notional_size: Dollar amount to buy
            
        Returns:
            dict: Order execution result
        """
        try:
            # Use market_open method for market buy orders
            result = self.exchange.market_open(
                name=symbol,
                is_buy=True,
                sz=float(notional_size)
            )
            return result
        except Exception as e:
            raise Exception(f"Failed to execute market buy for {symbol}: {e}")
    
    def market_sell(self, symbol: str, notional_size: float) -> Dict[str, Any]:
        """
        Execute a market sell order.
        
        Args:
            symbol: Trading symbol (e.g., "BTC", "ETH")
            notional_size: Dollar amount to sell
            
        Returns:
            dict: Order execution result
        """
        try:
            # Use market_open method for market sell orders
            result = self.exchange.market_open(
                name=symbol,
                is_buy=False,
                sz=float(notional_size)
            )
            return result
        except Exception as e:
            raise Exception(f"Failed to execute market sell for {symbol}: {e}")
    
    def limit_order(self, symbol: str, is_buy: bool, size: float, price: float) -> Dict[str, Any]:
        """
        Place a limit order.
        
        Args:
            symbol: Trading symbol
            is_buy: True for buy, False for sell
            size: Order size
            price: Limit price
            
        Returns:
            dict: Order placement result
        """
        try:
            result = self.exchange.order(
                name=symbol,
                is_buy=is_buy,
                sz=size,
                limit_px=price,
                order_type={"limit": {"tif": "Gtc"}}
            )
            return result
        except Exception as e:
            order_type = "buy" if is_buy else "sell"
            raise Exception(f"Failed to place {order_type} limit order for {symbol}: {e}")
    
    # ============================================================================
    # 3. PORTFOLIO & BALANCE QUERIES
    # ============================================================================
    
    def get_portfolio(self) -> Dict[str, Any]:
        """
        Get complete portfolio information.
        
        Returns:
            dict: Portfolio data
        """
        try:
            # Using user_state method which is the correct API method
            user_state = self.info.user_state(self.account_address)
            return user_state
        except Exception as e:
            raise Exception(f"Failed to fetch portfolio data: {e}")
    
    def get_equity(self) -> float:
        """
        Get current account equity/total value.
        
        Returns:
            float: Current equity in USD
        """
        try:
            # Using user_state method and extracting relevant equity value
            user_state = self.info.user_state(self.account_address)
            
            # Extract equity information based on the actual API response structure
            if user_state and "crossMarginSummary" in user_state:
                return float(user_state["crossMarginSummary"]["accountValue"])
            
            # Alternative paths to find equity value
            if user_state and "marginSummary" in user_state:
                return float(user_state["marginSummary"]["accountValue"])
            
            # Fallback - try to find account value in the response
            if user_state and "accountValue" in user_state:
                return float(user_state["accountValue"])
                
            return 0.0
        except Exception as e:
            raise Exception(f"Failed to fetch equity: {e}")
    
    def get_margin_summary(self) -> Dict[str, Any]:
        """
        Get margin summary including account value, margin used, etc.
        
        Returns:
            dict: Margin summary data
        """
        try:
            user_state = self.info.user_state(self.account_address)
            
            # Try different paths to find margin summary
            if user_state and "crossMarginSummary" in user_state:
                return user_state["crossMarginSummary"]
            if user_state and "marginSummary" in user_state:
                return user_state["marginSummary"]
                
            return {}
        except Exception as e:
            raise Exception(f"Failed to fetch margin summary: {e}")
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get current open positions.
        
        Returns:
            list: Current positions data
        """
        try:
            # Using user_state to get positions
            user_state = self.info.user_state(self.account_address)
            
            # Extract positions based on the actual API response structure
            if user_state and "assetPositions" in user_state:
                return user_state["assetPositions"]
            
            # Alternative paths to find positions
            if user_state and "positions" in user_state:
                return user_state["positions"]
                
            return []
        except Exception as e:
            raise Exception(f"Failed to fetch positions: {e}")
    
    def get_balance(self) -> Dict[str, float]:
        """
        Get wallet balances for different assets.
        
        Returns:
            dict: Asset balances
        """
        try:
            # Use the correct spotClearinghouseState endpoint
            response = requests.post(
                f"{self.base_url}/info",
                json={"type": "spotClearinghouseState", "user": self.account_address},
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract balances from the response
            if "balances" in data:
                return {balance["coin"]: float(balance["total"]) for balance in data["balances"]}
            return {}
        except Exception as e:
            raise Exception(f"Failed to fetch balances: {e}")
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def get_exchange_info(self) -> Dict[str, Any]:
        """
        Get exchange information including available markets.
        
        Returns:
            dict: Exchange metadata
        """
        try:
            meta = self.info.meta()
            return meta
        except Exception as e:
            raise Exception(f"Failed to fetch exchange info: {e}")
    
    def health_check(self) -> bool:
        """
        Perform a basic health check of the API connection.
        
        Returns:
            bool: True if API is accessible
        """
        try:
            # Try to fetch mid-prices as a health check
            self.get_all_mids()
            return True
        except Exception:
            return False


# ============================================================================
# EXAMPLE USAGE AND DEMO FUNCTIONS
# ============================================================================

async def demo_streaming(client: HyperClient, symbol: str = "BTC", duration: int = 30):
    """
    Demo function to stream trades for a limited time using the detailed_trade_data_handler.
    """
    print(f"[hyperliquid_client.demo_streaming] Starting trade stream for {symbol} (duration: {duration}s) using DETAILED handler.")
    
    # Using the imported detailed_trade_data_handler as the callback
    custom_callback = detailed_trade_data_handler 
    
    try:
        await asyncio.wait_for(
            client.stream_trades(symbol, custom_callback),
            timeout=duration
        )
    except asyncio.TimeoutError:
        print(f"[hyperliquid_client.demo_streaming] Trade streaming for {symbol} ended after {duration} seconds.")
    except Exception as e:
        print(f"[hyperliquid_client.demo_streaming] Error during demo_streaming for {symbol}: {e}")
        traceback.print_exc()


def main_demo():
    """
    Demo function showing basic usage of the HyperClient.
    
    Note: Replace with your actual credentials and set testnet=True for testing.
    """
    # IMPORTANT: Replace these with your actual credentials
    ACCOUNT_ADDRESS = "YOUR_ACCOUNT_ADDRESS_HERE"  # Your main wallet address (0x...)
    API_SECRET = "YOUR_API_SECRET_HERE"  # Your API wallet private key
    
    # Initialize client (use testnet=True for testing)
    try:
        client = HyperClient(ACCOUNT_ADDRESS, API_SECRET, testnet=True)
        print("✅ Hyperliquid client initialized successfully")
        
        # Health check
        if client.health_check():
            print("✅ API connection healthy")
        else:
            print("❌ API connection issues")
            return
        
        # 1. Get price data
        print("\n--- PRICE DATA ---")
        btc_price = client.get_mid_price("BTC")
        print(f"BTC mid-price: ${btc_price:,.2f}")
        
        eth_price = client.get_mid_price("ETH")
        print(f"ETH mid-price: ${eth_price:,.2f}")
        
        # 2. Portfolio information
        print("\n--- PORTFOLIO INFO ---")
        
        # Test portfolio query with proper error handling
        try:
            portfolio = client.get_portfolio()
            print(f"Portfolio data retrieved successfully")
            print(f"Portfolio keys: {list(portfolio.keys()) if portfolio else 'None'}")
        except Exception as e:
            print(f"Portfolio query failed: {e}")
        
        try:
            equity = client.get_equity()
            print(f"Current equity: ${equity:,.2f}")
        except Exception as e:
            print(f"Equity query failed: {e}")
        
        try:
            margin_summary = client.get_margin_summary()
            if margin_summary:
                account_value = margin_summary.get("accountValue", "N/A")
                print(f"Account value: ${account_value}")
            else:
                print("No margin summary available")
        except Exception as e:
            print(f"Margin summary query failed: {e}")
        
        try:
            positions = client.get_positions()
            print(f"Open positions: {len(positions) if positions else 0}")
            if positions:
                for pos in positions[:3]:  # Show first 3 positions
                    print(f"  Position: {pos}")
        except Exception as e:
            print(f"Positions query failed: {e}")

        # 2.5. Available API methods
        print("\n--- AVAILABLE API METHODS ---")
        
        # Collect all available methods
        api_methods = {}
        
        # Info API methods
        info_methods = [method for method in dir(client.info) if not method.startswith('_') and callable(getattr(client.info, method))]
        api_methods['Info API'] = sorted(info_methods)
        
        # Exchange API methods (if available)
        if hasattr(client, 'exchange') and client.exchange:
            exchange_methods = [method for method in dir(client.exchange) if not method.startswith('_') and callable(getattr(client.exchange, method))]
            api_methods['Exchange API'] = sorted(exchange_methods)
        
        # Client methods
        client_methods = [method for method in dir(client) if not method.startswith('_') and callable(getattr(client, method))]
        api_methods['Client Methods'] = sorted(client_methods)
        
        # Write to file
        with open('hyperliquid_api_methods.txt', 'w') as f:
            f.write("Hyperliquid API Methods\n")
            f.write("=" * 50 + "\n\n")
            
            for category, methods in api_methods.items():
                f.write(f"{category}:\n")
                f.write("-" * len(category) + "\n")
                for method in methods:
                    f.write(f"  - {method}\n")
                f.write("\n")
        
        print("✅ API methods saved to 'hyperliquid_api_methods.txt'")
        print(f"Total methods found: {sum(len(methods) for methods in api_methods.values())}")
        
        # 3. Trading (commented out for safety - uncomment to test)
        # print("\n--- TRADING (TESTNET ONLY) ---")
        # if client.testnet:
        #     try:
        #         result = client.market_buy("BTC", 10)  # Buy $10 of BTC
        #         print(f"Market buy result: {result}")
        #     except Exception as e:
        #         print(f"Trade failed: {e}")
        
        # 4. Streaming demo (commented out for safety - uncomment to test)
        # print("\n--- STREAMING DEMO ---")
        # asyncio.run(demo_streaming(client, "BTC", 10))
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main_demo() 