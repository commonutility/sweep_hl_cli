#!/usr/bin/env python3
"""
Hyperliquid Trading Demo

Simple demo of trading functionality:
1. Market Buy
2. Market Sell  
3. Limit Orders

USES REAL CREDENTIALS ON TESTNET
"""

import time
import json
from hyperliquid_client import HyperClient

def trading_demo():
    """
    Demo trading functionality with real orders.
    """
    # User credentials
    ACCOUNT_ADDRESS = "0x9CC9911250CE5868CfA8149f3748F655A368e890"
    API_SECRET = "0x1a1a291aa2725b9c6422d60b7bb73bb45f4b6c65fda7a1a3f0f4466ca728c79d"
    
    print("🚀 Hyperliquid Trading Demo")
    print("=" * 50)
    
    # Initialize client (TESTNET for safety)
    try:
        client = HyperClient(ACCOUNT_ADDRESS, API_SECRET, testnet=True)
        print("✅ Client initialized on TESTNET")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return
    
    # Get current prices
    try:
        btc_price = client.get_mid_price("BTC")
        eth_price = client.get_mid_price("ETH")
        sol_price = client.get_mid_price("SOL")
        
        print(f"\n📊 Current Prices:")
        print(f"   BTC: ${btc_price:,.2f}")
        print(f"   ETH: ${eth_price:,.2f}")
        print(f"   SOL: ${sol_price:,.2f}")
        
    except Exception as e:
        print(f"❌ Failed to get prices: {e}")
        return
    
    # Show current equity
    try:
        equity = client.get_equity()
        print(f"\n💰 Current Equity: ${equity:,.2f}")
    except Exception as e:
        print(f"💰 Current Equity: Unable to fetch (${e})")
    
    print(f"\n⚠️  READY TO TRADE ON TESTNET ⚠️")
    print(f"Account: {ACCOUNT_ADDRESS}")
    
    # Test 1: Market Buy
    print(f"\n🟢 TEST 1: Market Buy SOL")
    input("Press Enter to buy $5 worth of SOL...")
    
    try:
        result = client.market_buy("SOL", 5)
        print(f"✅ Market Buy Result:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"❌ Market buy failed: {e}")
    
    time.sleep(2)
    
    # Test 2: Limit Order  
    print(f"\n🔵 TEST 2: Limit Buy Order")
    limit_price = sol_price * 0.95  # 5% below current price
    print(f"Placing limit buy at ${limit_price:.2f} (5% below current)")
    input("Press Enter to place $3 limit buy order...")
    
    try:
        result = client.limit_order("SOL", True, 3, limit_price)
        print(f"✅ Limit Order Result:")
        print(json.dumps(result, indent=2))
        
        # Extract order ID for potential cancellation
        order_id = None
        if isinstance(result, dict) and "response" in result:
            response = result["response"]
            if "data" in response and "statuses" in response["data"]:
                statuses = response["data"]["statuses"]
                if statuses and len(statuses) > 0:
                    status = statuses[0]
                    if "resting" in status:
                        order_id = status["resting"]["oid"]
                        print(f"📝 Order ID: {order_id}")
        
        # Ask about canceling the limit order
        if order_id:
            cancel = input(f"\nCancel this limit order? (y/N): ").strip().lower()
            if cancel == 'y':
                try:
                    cancel_result = client.exchange.cancel("SOL", order_id)
                    print(f"✅ Cancel Result:")
                    print(json.dumps(cancel_result, indent=2))
                except Exception as e:
                    print(f"❌ Cancel failed: {e}")
        
    except Exception as e:
        print(f"❌ Limit order failed: {e}")
    
    time.sleep(2)
    
    # Test 3: Market Sell
    print(f"\n🔴 TEST 3: Market Sell SOL")
    input("Press Enter to sell $3 worth of SOL...")
    
    try:
        result = client.market_sell("SOL", 3)
        print(f"✅ Market Sell Result:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"❌ Market sell failed: {e}")
    
    # Final equity check
    try:
        final_equity = client.get_equity()
        print(f"\n💰 Final Equity: ${final_equity:,.2f}")
    except Exception as e:
        print(f"💰 Final Equity: Unable to fetch")
    
    print(f"\n🎉 Trading demo completed!")


if __name__ == "__main__":
    trading_demo() 