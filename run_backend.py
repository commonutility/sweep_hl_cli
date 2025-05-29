#!/usr/bin/env python3
"""
Run the backend server with network selection.

Usage:
    python run_backend.py                  # Runs on testnet (default)
    python run_backend.py --mainnet        # Runs on mainnet
    python run_backend.py --testnet        # Runs on testnet (explicit)
    
Environment variables:
    HYPERLIQUID_NETWORK: Set to 'mainnet' or 'testnet' (overrides command line)
    HYPERLIQUID_ACCOUNT_ADDRESS: Your account address
    HYPERLIQUID_MAINNET_API_SECRET: Your mainnet API secret
    HYPERLIQUID_TESTNET_API_SECRET: Your testnet API secret
"""

import sys
import os
import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser(description='Run the Hyperliquid Trading Assistant backend')
    network_group = parser.add_mutually_exclusive_group()
    network_group.add_argument('--mainnet', action='store_true', help='Run on mainnet')
    network_group.add_argument('--testnet', action='store_true', help='Run on testnet (default)')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on (default: 8000)')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    
    args = parser.parse_args()
    
    # Determine network
    if args.mainnet:
        network = 'mainnet'
    elif args.testnet:
        network = 'testnet'
    else:
        # Default to testnet if not specified
        network = 'testnet'
    
    # Set environment variable if not already set
    if 'HYPERLIQUID_NETWORK' not in os.environ:
        os.environ['HYPERLIQUID_NETWORK'] = network
    
    print(f"Starting Hyperliquid Trading Assistant Backend on {network.upper()}")
    print(f"Server will run on http://{args.host}:{args.port}")
    print()
    
    # Check for required environment variables
    if network == 'mainnet' and not os.environ.get('HYPERLIQUID_MAINNET_API_SECRET'):
        print("WARNING: HYPERLIQUID_MAINNET_API_SECRET not set. You won't be able to execute trades on mainnet.")
        print()
    
    # Run the migration first
    print("Checking database migration...")
    try:
        subprocess.run([sys.executable, 'migrate_database.py'], check=True)
    except subprocess.CalledProcessError:
        print("Database migration failed. Please check the error above.")
        sys.exit(1)
    except FileNotFoundError:
        print("Note: migrate_database.py not found. Skipping migration.")
    
    print()
    
    # Change to backend directory
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
    os.chdir(backend_dir)
    
    # Run uvicorn
    cmd = [
        sys.executable, '-m', 'uvicorn',
        'main:app',
        '--host', args.host,
        '--port', str(args.port),
        '--reload'
    ]
    
    print(f"Running: {' '.join(cmd)}")
    print()
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nShutting down server...")

if __name__ == '__main__':
    main() 