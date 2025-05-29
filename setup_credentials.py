#!/usr/bin/env python3
"""
Interactive script to help set up Hyperliquid credentials.
"""

import os
import yaml
from pathlib import Path
import getpass

def main():
    print("Hyperliquid Trading Assistant - Credentials Setup")
    print("=" * 50)
    print()
    
    # Check if credentials.yaml already exists
    creds_path = Path("credentials.yaml")
    if creds_path.exists():
        overwrite = input("credentials.yaml already exists. Overwrite? (y/N): ").lower()
        if overwrite != 'y':
            print("Setup cancelled.")
            return
    
    print("This script will help you set up your API credentials.")
    print("Your credentials will be saved to credentials.yaml")
    print("Make sure this file is in .gitignore!\n")
    
    # Get account address
    print("Step 1: Account Address")
    print("This is your Ethereum wallet address (same for both networks)")
    account_address = input("Enter your wallet address (0x...): ").strip()
    
    if not account_address.startswith("0x") or len(account_address) != 42:
        print("Warning: Address should start with 0x and be 42 characters long")
    
    print()
    
    # Get testnet credentials
    print("Step 2: Testnet API Secret")
    print("To get your testnet secret:")
    print("1. Go to https://testnet.hyperliquid.xyz")
    print("2. Connect wallet → Click address → API Wallet → Generate/Copy key")
    print()
    
    use_default_testnet = input("Use default testnet credentials? (Y/n): ").lower()
    if use_default_testnet == 'n':
        testnet_secret = getpass.getpass("Enter your testnet API secret (hidden): ").strip()
    else:
        testnet_secret = "0xd05c9314fbd68b22b5e0a1b4f0291bfffa82bad625dab18bc1aaee97281fcc08"
        print("Using default testnet credentials")
    
    print()
    
    # Get mainnet credentials
    print("Step 3: Mainnet API Secret (Optional)")
    print("⚠️  WARNING: Mainnet uses REAL FUNDS!")
    print("To get your mainnet secret:")
    print("1. Go to https://app.hyperliquid.xyz")
    print("2. Connect wallet → Click address → API Wallet → Generate/Copy key")
    print()
    
    setup_mainnet = input("Set up mainnet credentials now? (y/N): ").lower()
    if setup_mainnet == 'y':
        mainnet_secret = getpass.getpass("Enter your mainnet API secret (hidden): ").strip()
    else:
        mainnet_secret = ""
        print("Skipping mainnet setup. You can add it later to credentials.yaml")
    
    print()
    
    # Get default network
    print("Step 4: Default Network")
    default_network = input("Default network (testnet/mainnet) [testnet]: ").lower() or "testnet"
    
    if default_network not in ["testnet", "mainnet"]:
        print("Invalid network. Using testnet as default.")
        default_network = "testnet"
    
    # Create credentials dictionary
    credentials = {
        "account_address": account_address,
        "api_secrets": {
            "mainnet": mainnet_secret,
            "testnet": testnet_secret
        },
        "settings": {
            "default_network": default_network,
            "max_position_size": 1000,
            "require_confirmation": True
        }
    }
    
    # Save to file
    with open(creds_path, 'w') as f:
        yaml.dump(credentials, f, default_flow_style=False, sort_keys=False)
    
    print()
    print("✅ Credentials saved to credentials.yaml")
    print()
    print("Next steps:")
    print("1. Start the backend: python run_backend.py")
    print("2. Start the frontend: cd frontend && npm run dev")
    print("3. Visit http://localhost:5170")
    print()
    print("Remember: NEVER commit credentials.yaml to version control!")

if __name__ == "__main__":
    main() 