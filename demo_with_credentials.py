#!/usr/bin/env python3
"""
Hyperliquid Demo Script - Full Trading Workflow (Testnet)
"""

import asyncio
import os
import traceback
import time
import json

# Import from the installed hyperliquid_wrapper package
from hyperliquid_wrapper.api.hyperliquid_client import HyperClient
# Import the specific fill handler we created and the new cancel response handler
from hyperliquid_wrapper.data_handlers.fill_handler import user_fill_handler, handle_cancel_order_response 
# Import database manager functions
from hyperliquid_wrapper.database_handlers.database_manager import (
    initialize_database, get_current_positions, get_all_trades,
    add_open_order, remove_open_order, get_tracked_open_orders
)

# Main account address (ensure this is a TESTNET account if sending real trades)
# For this demo, we'll use environment variables or a default testnet address.
ACCOUNT_ADDRESS = os.getenv("HYPERLIQUID_ACCOUNT_ADDRESS", "0x9CC9911250CE5868CfA8149f3748F655A368e890")

# API Secret Key for TESTNET
TESTNET_API_SECRET = os.getenv("HYPERLIQUID_TESTNET_API_SECRET", "0xd05c9314fbd68b22b5e0a1b4f0291bfffa82bad625dab18bc1aaee97281fcc08")

async def trading_workflow_demo():
    """Demonstrates the full workflow: init DB, send trade, get fill via WebSocket, store in DB."""
    print("--- FULL TRADING WORKFLOW DEMO (TESTNET) ---")

    # --- 1. Initialize Database ---
    print("\n[STAGE 1] Initializing Database...")
    try:
        initialize_database()
        print("[STAGE 1] Database initialized successfully.")
    except Exception as e_db_init:
        print(f"[STAGE 1] ERROR initializing database: {e_db_init}")
        traceback.print_exc()
        return # Stop demo if DB fails

    # --- 2. Initialize HyperClient for Testnet ---
    print("\n[STAGE 2] Initializing HyperClient for Testnet...")
    if not TESTNET_API_SECRET or TESTNET_API_SECRET == "YOUR_TESTNET_API_SECRET_HERE":
        print("[STAGE 2] ERROR: TESTNET_API_SECRET not set. Please set the environment variable HYPERLIQUID_TESTNET_API_SECRET.")
        print("             Using a placeholder secret will likely result in authentication failure.")
        # return # Optional: stop if no secret
    
    client = HyperClient(ACCOUNT_ADDRESS, TESTNET_API_SECRET, testnet=True)
    print(f"[STAGE 2] HyperClient initialized for Testnet. Account: {ACCOUNT_ADDRESS}")

    # --- 3. Send a Test Trade (e.g., small market buy of BTC-PERP) ---
    # Ensure the symbol and size are appropriate for Testnet and your account balance
    trade_symbol = "BTC" # Using BTC as it's common on testnet
    # CAUTION: Using a notional size. For actual size in asset terms, you'd calculate based on price.
    # Example: 0.001 BTC. If BTC is $50k, notional is $50. Adjust sz accordingly for market_open if it expects asset size.
    # The SDK's market_open `sz` is in terms of the asset, not notional USD for perp. Let's use a small asset size.
    trade_notional_size = 10 # USD notional for the trade
    trade_asset_size = 0.0002 # Approx $10 if BTC is $50k, adjust as needed for testnet

    print(f"\n[STAGE 3] Attempting to send a test market buy order on Testnet...")
    print(f"          Order: BUY {trade_asset_size} {trade_symbol}")
    order_result = None
    placed_order_id = None # Variable to store the ID of the placed order
    try:
        # First, get current price to estimate asset size for a $10 notional trade
        print(f"          Fetching current mid price for {trade_symbol} to calculate asset size for ${trade_notional_size} notional...")
        current_price = client.get_mid_price(trade_symbol)
        print(f"          Current mid price for {trade_symbol}: ${current_price}")
        trade_asset_size_calculated = trade_notional_size / current_price
        print(f"          Calculated asset size for ${trade_notional_size} notional: {trade_asset_size_calculated:.6f} {trade_symbol}")
        
        # Using a small fixed asset size to simplify and avoid large testnet orders if price is low
        # Ensure this is a very small amount for testing.
        fixed_test_asset_size = 0.0001 
        print(f"          Using fixed asset size for test trade: {fixed_test_asset_size} {trade_symbol}")

        order_result = client.market_buy(symbol=trade_symbol, asset_size=fixed_test_asset_size)
        print(f"[STAGE 3] Market buy order sent successfully (or at least accepted by API). Response:")
        print(json.dumps(order_result, indent=2))
        
        # Extract Order ID and log to open_orders_tracking
        if order_result and isinstance(order_result, dict) and order_result.get('status') == 'ok':
            response_block = order_result.get('response')
            if response_block and isinstance(response_block, dict):
                data_block = response_block.get('data')
                if data_block and isinstance(data_block, dict):
                    statuses = data_block.get('statuses')
                    if statuses and isinstance(statuses, list) and len(statuses) > 0:
                        first_status = statuses[0]
                        if isinstance(first_status, dict):
                            order_id_to_track = None
                            order_status_type = None # 'filled' or 'resting'

                            if 'filled' in first_status and isinstance(first_status['filled'], dict):
                                order_id_to_track = first_status['filled'].get('oid')
                                order_status_type = 'filled'
                                print(f"          Order filled. Order ID: {order_id_to_track}")
                            elif 'resting' in first_status and isinstance(first_status['resting'], dict):
                                order_id_to_track = first_status['resting'].get('oid')
                                order_status_type = 'resting'
                                print(f"          Order is resting. Order ID: {order_id_to_track}")
                            
                            if order_id_to_track:
                                placed_order_id = order_id_to_track # Keep this for cancellation logic
                                open_order_details = {
                                    "order_id": order_id_to_track,
                                    "symbol": trade_symbol,
                                    "side": "B", # Assuming market_buy
                                    "order_type": "market", # Or more specifically based on order_result if available
                                    "price": first_status.get(order_status_type, {}).get('avgPx') if order_status_type == 'filled' else None, # Price if filled
                                    "size": fixed_test_asset_size,
                                    "timestamp_placed": int(time.time() * 1000)
                                }
                                add_open_order(open_order_details)
                                # If the order is 'filled' immediately in the synchronous response,
                                # we might consider removing it from open_orders_tracking right away.
                                # However, the fill handler will also attempt this based on WebSocket fill.
                                # For simplicity now, let fill_handler manage removal on fill.
                                if order_status_type == 'filled':
                                    print(f"          Order ID {order_id_to_track} was filled immediately. It will be removed from open_orders_tracking upon WebSocket fill processing.")
                            else:
                                print("          Order status in response not 'filled' or 'resting', or oid not found.")
    except Exception as e_trade:
        print(f"[STAGE 3] ERROR sending market buy order: {e_trade}")
        traceback.print_exc()
        # Not returning, will still try to listen for fills in case order went through partially or later

    # --- 4. Subscribe to User Fills via WebSocket ---
    print("\n[STAGE 4] Subscribing to userFills WebSocket stream...")
    print(f"          Using handler: {user_fill_handler.__name__}")
    stream_duration = 20  # seconds to listen for fills

    try:
        print(f"          Will listen for fills for {stream_duration} seconds...")
        # The stream_user_fills method uses user_fill_handler by default
        await asyncio.wait_for(client.stream_user_fills(), timeout=stream_duration)
        print(f"[STAGE 4] WebSocket stream for userFills finished after {stream_duration}s (timeout). Handler should have processed any fills.")
    except asyncio.TimeoutError:
        print(f"[STAGE 4] WebSocket stream for userFills automatically timed out after {stream_duration} seconds as planned.")
    except Exception as e_ws:
        print(f"[STAGE 4] ERROR during WebSocket userFills streaming: {e_ws}")
        traceback.print_exc()
    
    print("[STAGE 4] WebSocket subscription part finished.")

    # --- Try to Cancel the Order ---
    if placed_order_id:
        print(f"\n[STAGE 4.5] Attempting to cancel order ID {placed_order_id} for {trade_symbol}...")
        try:
            cancel_result = client.cancel_order(symbol=trade_symbol, order_id=placed_order_id)
            # Use the dedicated handler from fill_handler.py
            handle_cancel_order_response(cancel_result, placed_order_id)
        except Exception as e_cancel:
            print(f"[STAGE 4.5] ERROR attempting to cancel order ID {placed_order_id}: {e_cancel}")
            traceback.print_exc()
    else:
        print("\n[STAGE 4.5] No order ID was captured, skipping cancellation attempt.")

    # --- 5. Display Stored Data ---
    print("\n[STAGE 5] Displaying data from database...")
    try:
        print("\n  Current Positions:")
        current_positions = get_current_positions()
        if current_positions:
            for pos in current_positions:
                print(f"    Coin: {pos['coin']}, Net Size: {pos['net_size']:.6f}, Avg Entry: {pos['average_entry_price']:.2f}")
        else:
            print("    No open positions found in the database.")

        print("\n  All Trades (most recent first):")
        all_trades_from_db = get_all_trades()
        if all_trades_from_db:
            for trade_db in all_trades_from_db[:5]: # Show up to 5 most recent
                print(f"    Trade ID: {trade_db['trade_id']}, Coin: {trade_db['coin']}, Dir: {trade_db['dir']}, Sz: {trade_db['size']}, Px: {trade_db['price']}")
        else:
            print("    No trades found in the database.")

        print("\n  Tracked Open Orders (at end of demo):")
        tracked_open_orders = get_tracked_open_orders()
        if tracked_open_orders:
            for open_order in tracked_open_orders:
                print(f"    Order ID: {open_order['order_id']}, Symbol: {open_order['symbol']}, Side: {open_order['side']}, Type: {open_order['order_type']}, Size: {open_order['size']}, Px: {open_order.get('price', 'N/A')}")
        else:
            print("    No orders found in open_orders_tracking table.")

    except Exception as e_db_read:
        print(f"[STAGE 5] ERROR reading from database: {e_db_read}")
        traceback.print_exc()

    print("\n--- FULL TRADING WORKFLOW DEMO COMPLETED ---")

if __name__ == "__main__":
    print("NOTE: Ensure your HYPERLIQUID_ACCOUNT_ADDRESS and HYPERLIQUID_TESTNET_API_SECRET environment variables are set.")
    print("      This demo will attempt to place a SMALL market order on TESTNET.")
    print("      The database will be created in a 'database' subdirectory if it doesn't exist.")
    print("-------------------------------------------------------------------------------------------")
    
    
    asyncio.run(trading_workflow_demo()) 