#!/usr/bin/env python3
"""
Reasoning Demo Script - Takes user input and simulates LLM processing.
"""

import asyncio
import os
import traceback
import time

# Imports from hyperliquid_wrapper package
from src.hyperliquid_wrapper.api.hyperliquid_client import HyperClient
from src.hyperliquid_wrapper.database_handlers.database_manager import initialize_database, get_current_positions, get_all_trades, get_tracked_open_orders

# Imports from reasoning package
from src.reasoning.llm_client import LLMClient

# Credentials (use environment variables with defaults for safety)
ACCOUNT_ADDRESS = os.getenv("HYPERLIQUID_ACCOUNT_ADDRESS", "0x9CC9911250CE5868CfA8149f3748F655A368e890")
TESTNET_API_SECRET = os.getenv("HYPERLIQUID_TESTNET_API_SECRET", "0xd05c9314fbd68b22b5e0a1b4f0291bfffa82bad625dab18bc1aaee97281fcc08") # Ensure this is a valid TESTNET secret

async def main_reasoning_demo():
    """Main function for the reasoning demo."""
    print("--- Hyperliquid Reasoning Demo --- ")
    print("This demo will take your text commands and simulate processing them with an LLM.")
    print("No actual trades will be placed or API calls made to LLM in this version.")
    print("Ensure your OPENAI_API_KEY environment variable is set for LLM client initialization.")
    print("Hyperliquid Testnet credentials (HYPERLIQUID_ACCOUNT_ADDRESS, HYPERLIQUID_TESTNET_API_SECRET) are used for client setup.")
    print("------------------------------------------------------------------------------------------------")

    # 1. Initialize Database (shared with other demos)
    print("\n[SYSTEM] Initializing Database...")
    try:
        initialize_database()
        print("[SYSTEM] Database initialized successfully.")
    except Exception as e_db_init:
        print(f"[SYSTEM] ERROR initializing database: {e_db_init}")
        traceback.print_exc()
        # Continue without DB if needed for LLM part, or return

    # 2. Initialize OpenAI Client
    print("\n[SYSTEM] Initializing OpenAI Client...")
    llm_service = LLMClient() # Instantiate the class
    
    if not llm_service.is_ready(): # Check if client is ready
        print("[SYSTEM] WARNING: OpenAI client failed to initialize or is not ready. LLM features will be unavailable.")
        # Depending on requirements, you might want to exit here or have a fallback.
    else:
        print("[SYSTEM] OpenAI client seems ready.")

    # 3. Initialize HyperClient for Testnet (not strictly used yet, but good for future steps)
    print("\n[SYSTEM] Initializing HyperClient for Testnet...")
    if not TESTNET_API_SECRET or TESTNET_API_SECRET == "0xd05c9314fbd68b22b5e0a1b4f0291bfffa82bad625dab18bc1aaee97281fcc08":
        print("[SYSTEM] WARNING: Using default/placeholder TESTNET_API_SECRET.")
        print("          Ensure HYPERLIQUID_TESTNET_API_SECRET is set correctly for future Hyperliquid interactions.")
    
    # This client is not used to make calls in this version, but set up for future integration
    hl_client = HyperClient(ACCOUNT_ADDRESS, TESTNET_API_SECRET, testnet=True) 
    print(f"[SYSTEM] HyperClient initialized for Testnet. Account: {ACCOUNT_ADDRESS} (not actively used in this demo version).")

    # 4. User Input Loop
    print("\nEnter your commands for Hyperliquid Testnet below.")
    print("Type 'exit' to quit.")
    
    while True:
        try:
            user_input = input("\nYour command > ")
            if user_input.strip().lower() == 'exit':
                print("[SYSTEM] Exiting reasoning demo.")
                break
            if not user_input.strip():
                continue

            # Call the LLM for a direct chat response
            if llm_service.is_ready():
                llm_response = llm_service.get_llm_chat_response(user_input)
                print("\n[LLM RESPONSE]") 
                if llm_response and isinstance(llm_response, dict):
                    if llm_response.get("status") == "success":
                        print(f"  LLM: {llm_response.get('llm_response_text')}")
                    else:
                        print(f"  Error from LLMClient: {llm_response.get('status')}")
                        if llm_response.get('error_message'):
                            print(f"    Details: {llm_response.get('error_message')}")
                else:
                    print("  No valid response object from LLMClient.")
            else:
                print("\n[SYSTEM] OpenAI client not ready, cannot process command with LLM.")
            
            # Future steps would be to re-implement tool calling logic here
            # based on a different method from LLMClient designed for tool use.

        except KeyboardInterrupt:
            print("\n[SYSTEM] Keyboard interrupt detected. Exiting...")
            break
        except Exception as e_loop:
            print(f"[SYSTEM] An error occurred in the command loop: {e_loop}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main_reasoning_demo()) 