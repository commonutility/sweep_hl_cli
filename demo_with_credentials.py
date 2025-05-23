#!/usr/bin/env python3
"""
Hyperliquid Demo Script with Mainnet (Read-Only) and Testnet (Trading) options.
"""

import time
import json
import asyncio # For WebSocket demo
import traceback

from hyperliquid_client import HyperClient # Assuming demo_streaming is no longer directly imported if it was
# Import the specific handler we want to use for the demo
from model_handlers.model_stream_handler import detailed_trade_data_handler 

# Main account address (same for both Mainnet and Testnet interactions)
ACCOUNT_ADDRESS = "0x9CC9911250CE5868CfA8149f3748F655A368e890"

# API Secret Keys - IMPORTANT: Ensure these are the correct keys for the respective networks
MAINNET_API_SECRET = "0x8bd5db8db0c5c5e828a1847518da0b8b33cfafce30ce68493bf79408400bf52b" # Believed to be Mainnet key
TESTNET_API_SECRET = "0xd05c9314fbd68b22b5e0a1b4f0291bfffa82bad625dab18bc1aaee97281fcc08"  # Provided as Testnet key

def mainnet_readonly_demo():
    """
    Connects to Mainnet and fetches read-only authenticated account data.
    NO TRADES WILL BE EXECUTED.
    """
    print("\n🚀 Hyperliquid MAINNET Read-Only Demo")
    print("=" * 60)
    print("⚠️  CONNECTING TO MAINNET - NO TRADES WILL BE EXECUTED ⚠️")
    
    try:
        client = HyperClient(ACCOUNT_ADDRESS, MAINNET_API_SECRET, testnet=False)
        print("✅ Client initialized on MAINNET")
    except Exception as e:
        print(f"❌ Failed to initialize Mainnet client: {e}")
        traceback.print_exc()
        return

    print("\n📡 Performing Health Check on Mainnet...")
    try:
        if client.health_check():
            print("✅ Mainnet API is healthy")
        else:
            print("❌ Mainnet API health check failed")
    except Exception as e:
        print(f"❌ Mainnet Health check error: {e}")

    print("\n📊 Fetching Your Account State from MAINNET...")
    try:
        user_state = client.get_portfolio()
        print("✅ Successfully fetched user_state from Mainnet:")
        print("-" * 40)
        print(json.dumps(user_state, indent=2, sort_keys=True))
        print("-" * 40)
        
        equity = client.get_equity()
        print(f"\n💰 Current Equity on Mainnet: ${equity:,.2f}")
        
        balances = client.get_balance()
        print("\n💳 Wallet Balances on Mainnet:")
        if balances:
            for asset, balance_val in balances.items():
                print(f"  {asset}: {balance_val}")
        else:
            print("  No spot balances found or query failed.")
            
    except Exception as e:
        print(f"❌ Failed to fetch user_state from Mainnet: {e}")
        traceback.print_exc()

    print("\n🎉 Mainnet read-only demo completed. NO TRADES WERE EXECUTED.")

def testnet_trading_demo():
    """
    Connects to Testnet and executes a sequence of trades.
    """
    print("\n🚀 Hyperliquid TESTNET Trading Demo")
    print("=" * 60)
    print("⚠️  CONNECTING TO TESTNET - Trades WILL be executed ⚠️")
    
    try:
        client = HyperClient(ACCOUNT_ADDRESS, TESTNET_API_SECRET, testnet=True)
        print("✅ Client initialized on TESTNET")
    except Exception as e:
        print(f"❌ Failed to initialize Testnet client: {e}")
        traceback.print_exc()
        return

    sol_price = 1.0 # Default if API fails
    try:
        sol_price = client.get_mid_price("SOL")
        print(f"\n📊 Current SOL Price on Testnet: ${sol_price:,.2f}")
    except Exception as e:
        print(f"❌ Failed to get SOL price on Testnet: {e}. Using default for limit order.")

    try:
        equity = client.get_equity()
        print(f"💰 Current Equity on Testnet: ${equity:,.2f}")
    except Exception as e:
        print(f"💰 Testnet Equity check failed: {e}")
        
    print(f"\nAccount: {ACCOUNT_ADDRESS}")
    trade_confirmation = input("ATTENTION: This will execute TEST trades. Continue? (y/N): ").strip().lower()
    if trade_confirmation != 'y':
        print("Testnet trading demo cancelled by user.")
        return

    print(f"\n🟢 TEST 1: Market Buy $1 worth of SOL on Testnet")
    try:
        buy_result = client.market_buy("SOL", 1)
        print(f"✅ Market Buy Result: {json.dumps(buy_result, indent=2)}")
    except Exception as e:
        print(f"❌ Market Buy Failed on Testnet: {e}")

    time.sleep(3)

    print(f"\n🔵 TEST 2: Place a Limit Buy Order for SOL on Testnet")
    limit_buy_price = sol_price * 0.95
    limit_buy_size_asset = 1.0 / limit_buy_price if limit_buy_price > 0 else 1.0
    print(f"   Attempting limit buy for {limit_buy_size_asset:.4f} SOL @ ${limit_buy_price:.2f}")
    try:
        limit_result = client.limit_order("SOL", True, limit_buy_size_asset, limit_buy_price)
        print(f"✅ Limit Order Result: {json.dumps(limit_result, indent=2)}")
        order_id = None
        if isinstance(limit_result, dict) and \
           limit_result.get("status") == "ok" and \
           isinstance(limit_result.get("response"), list) and \
           len(limit_result["response"]) > 0 and \
           isinstance(limit_result["response"][0], dict) and \
           isinstance(limit_result["response"][0].get("data"), dict) and \
           isinstance(limit_result["response"][0]["data"].get("statuses"), list) and \
           len(limit_result["response"][0]["data"]["statuses"]) > 0 and \
           isinstance(limit_result["response"][0]["data"]["statuses"][0], dict) and \
           "resting" in limit_result["response"][0]["data"]["statuses"][0]:
            resting_order = limit_result["response"][0]["data"]["statuses"][0].get("resting")
            if isinstance(resting_order, dict):
                order_id = resting_order.get("oid")
        if order_id is not None:
            print(f"📝 Limit Order ID: {order_id}")
            if input(f"Cancel limit order {order_id}? (y/N): ").lower() == 'y':
                client.exchange.cancel("SOL", order_id)
                print(f"Order {order_id} cancellation attempted.")
        else:
            print("ℹ️ Could not extract order ID for cancellation.")
    except Exception as e:
        print(f"❌ Limit Order Failed on Testnet: {e}")
        traceback.print_exc()

    time.sleep(3)

    print(f"\n🔴 TEST 3: Market Sell $1 worth of SOL on Testnet")
    try:
        sell_result = client.market_sell("SOL", 1)
        print(f"✅ Market Sell Result: {json.dumps(sell_result, indent=2)}")
    except Exception as e:
        print(f"❌ Market Sell Failed on Testnet: {e}")
        
    try:
        final_equity = client.get_equity()
        print(f"\n💰 Final Equity on Testnet: ${final_equity:,.2f}")
    except Exception as e:
        print(f"💰 Testnet Equity check failed: {e}")

    print("\n🎉 Testnet trading demo completed!")


async def run_websocket_demo(client: HyperClient, symbol: str, duration: int):
    """Helper async function to run the streaming demo."""
    print(f"[DemoScript] Starting trade stream for {symbol} (duration: {duration}s) using DETAILED handler.")
    await asyncio.wait_for(
        client.stream_trades(symbol, detailed_trade_data_handler), # Use imported handler
        timeout=duration
    )

if __name__ == "__main__":
    print("Which demo would you like to run?")
    print("1. Mainnet Read-Only Demo")
    print("2. Testnet Trading Demo")
    print("3. Testnet WebSocket Streaming Demo") # Added option for WS
    choice = input("Enter choice (1, 2, or 3): ").strip()

    if choice == '1':
        mainnet_readonly_demo()
    elif choice == '2':
        testnet_trading_demo()
    elif choice == '3':
        print("\n🌊 --- TESTNET WEBSOCKET STREAMING TEST ---")
        print("Initializing client for Testnet WebSocket streaming...")
        try:
            ws_client = HyperClient(ACCOUNT_ADDRESS, TESTNET_API_SECRET, testnet=True)
            symbol_to_stream = input("Enter symbol to stream (e.g., SOL, default BTC): ").strip().upper() or "BTC"
            stream_duration = int(input("Enter stream duration in seconds (e.g., 15): ").strip() or 15)
            
            asyncio.run(run_websocket_demo(ws_client, symbol_to_stream, stream_duration))
            print("✅ WebSocket streaming test completed.")
        except Exception as e_ws_setup:
            print(f"❌ Failed to setup or run WebSocket demo: {e_ws_setup}")
            traceback.print_exc()
    else:
        print("Invalid choice. Exiting.") 