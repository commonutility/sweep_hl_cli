#!/usr/bin/env python3
"""
Hyperliquid Demo Script - Focused WebSocket Test
"""

import asyncio
import traceback
# import sys # No longer needed
# import os  # No longer needed

# # Add project root to sys.path to allow absolute imports of sibling packages # No longer needed
# PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# sys.path.insert(0, PROJECT_ROOT)

# Import from the installed hyperliquid_wrapper package
from hyperliquid_wrapper.api.hyperliquid_client import HyperClient, demo_streaming
from hyperliquid_wrapper.model_handlers.model_stream_handler import detailed_trade_data_handler 

# Main account address
ACCOUNT_ADDRESS = "0x9CC9911250CE5868CfA8149f3748F655A368e890"

# API Secret Keys - Only Testnet needed for this focused demo
TESTNET_API_SECRET = "0xd05c9314fbd68b22b5e0a1b4f0291bfffa82bad625dab18bc1aaee97281fcc08"

# Define the other demo functions so they exist, but they won't be called.
def mainnet_readonly_demo():
    pass

def testnet_trading_demo():
    pass

async def run_focused_websocket_demo():
    """Runs the SOL WebSocket stream for 3 seconds on Testnet."""
    print("--- TESTNET WEBSOCKET STREAMING TEST (SOL, 3 seconds) ---")
    print("Initializing client for Testnet WebSocket streaming...")
    try:
        ws_client = HyperClient(ACCOUNT_ADDRESS, TESTNET_API_SECRET, testnet=True)
        
        # Directly call the imported demo_streaming from the client's module
        # It already uses detailed_trade_data_handler by default as per its definition.
        await demo_streaming(ws_client, "SOL", 3) 
        
        print("WebSocket streaming test for SOL (3s) completed.")
    except Exception as e_ws_setup:
        print(f"Failed to setup or run WebSocket demo: {e_ws_setup}")
        traceback.print_exc()

if __name__ == "__main__":
    print("NOTE: Before running, ensure you have installed the project in editable mode:")
    print("  pip install -e .")
    print("---------------------------------------------------------------------------")
    asyncio.run(run_focused_websocket_demo()) 