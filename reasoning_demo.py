#!/usr/bin/env python3
"""
Reasoning Demo Script - Takes user input and uses LLM for action decision.
"""

import asyncio
import os
import traceback
import time
import json # For printing dicts nicely

# Imports from hyperliquid_wrapper package
from src.hyperliquid_wrapper.api.hyperliquid_client import HyperClient
from src.hyperliquid_wrapper.database_handlers.database_manager import (
    initialize_database, get_current_positions, get_all_trades, get_tracked_open_orders
)

# Imports from reasoning package
from src.reasoning.llm_client import LLMClient 

# Credentials
ACCOUNT_ADDRESS = os.getenv("HYPERLIQUID_ACCOUNT_ADDRESS", "0x9CC9911250CE5868CfA8149f3748F655A368e890")
TESTNET_API_SECRET = os.getenv("HYPERLIQUID_TESTNET_API_SECRET", "0xd05c9314fbd68b22b5e0a1b4f0291bfffa82bad625dab18bc1aaee97281fcc08")

async def main_reasoning_demo():
    """Main function for the reasoning demo."""
    print("--- Hyperliquid Reasoning Demo with Tool Calling --- ")
    print("This demo will take your text commands, ask an LLM to decide on an action (tool call or text response),")
    print("and then execute database query tools or print the LLM's text.")
    print("Ensure your OPENAI_API_KEY environment variable is set.")
    print("------------------------------------------------------------------------------------------------")

    print("\n[SYSTEM] Initializing Database...")
    try:
        initialize_database()
        print("[SYSTEM] Database initialized successfully.")
    except Exception as e_db_init:
        print(f"[SYSTEM] ERROR initializing database: {e_db_init}")
        return

    print("\n[SYSTEM] Initializing LLMClient...")
    llm_service = LLMClient()
    if not llm_service.is_ready():
        print("[SYSTEM] CRITICAL ERROR: LLMClient failed to initialize or is not ready. Check OpenAI API key and logs. Exiting.")
        return
    print("[SYSTEM] LLMClient initialized successfully.")

    print("\n[SYSTEM] Initializing HyperClient for Testnet (for potential future tool calls)...")
    hl_client = HyperClient(ACCOUNT_ADDRESS, TESTNET_API_SECRET, testnet=True) 
    print(f"[SYSTEM] HyperClient initialized for Testnet. Account: {ACCOUNT_ADDRESS}")

    print("\nEnter your commands related to trades or positions (or type 'exit').")
    
    while True:
        try:
            user_input = input("\nYour command > ")
            if user_input.strip().lower() == 'exit':
                print("[SYSTEM] Exiting reasoning demo.")
                break
            if not user_input.strip():
                continue

            llm_action = llm_service.decide_action_with_llm(user_input)
            print(f"\n[LLM ACTION DECISION]: {json.dumps(llm_action, indent=2)}")

            if llm_action and isinstance(llm_action, dict):
                action_type = llm_action.get("type")
                if action_type == "tool_call":
                    function_name = llm_action.get("function_name")
                    arguments = llm_action.get("arguments", {})
                    print(f"[EXECUTION ENGINE] LLM decided to call tool: {function_name} with arguments: {arguments}")

                    # Execute the decided function
                    if function_name == "get_all_trades_from_db":
                        all_trades = get_all_trades()
                        print("\n[RESULT] All Trades from DB:")
                        if all_trades:
                            for trade in all_trades[:10]: # Print up to 10
                                print(f"  - {trade}")
                        else:
                            print("  No trades found in the database.")
                    elif function_name == "get_current_positions_from_db":
                        current_positions = get_current_positions()
                        print("\n[RESULT] Current Positions from DB:")
                        if current_positions:
                            for pos in current_positions:
                                print(f"  - {pos}")
                        else:
                            print("  No open positions found in the database.")
                    else:
                        print(f"[EXECUTION ENGINE] Error: Tool '{function_name}' is not recognized or implemented yet.")
                
                elif action_type == "text_response":
                    print(f"\n[LLM TEXT RESPONSE]: {llm_action.get('llm_response_text')}")
                
                elif action_type == "error":
                    print(f"\n[LLM CLIENT ERROR]: Status: {llm_action.get('status')}, Message: {llm_action.get('error_message')}")
                else:
                    print(f"\n[SYSTEM] Received an unexpected action type from LLMClient: {action_type}")

            else:
                print("\n[SYSTEM] Failed to get a valid action from LLMClient.")

        except KeyboardInterrupt:
            print("\n[SYSTEM] Keyboard interrupt detected. Exiting...")
            break
        except Exception as e_loop:
            print(f"[SYSTEM] An error occurred in the command loop: {e_loop}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main_reasoning_demo()) 