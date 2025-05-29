"""
Configuration management for the Hyperliquid Trading Assistant.
Handles network selection (mainnet/testnet) and other global settings.
"""

import os
import yaml
from enum import Enum
from typing import Optional, Dict, Any
from pathlib import Path

class Network(Enum):
    """Network types supported by the application."""
    MAINNET = "mainnet"
    TESTNET = "testnet"

class Config:
    """Global configuration singleton that reads from config.yaml and environment variables."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Load configuration from YAML file
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                self._config = yaml.safe_load(f)
        else:
            # Fallback configuration if YAML doesn't exist
            self._config = {
                "default_network": "testnet",
                "networks": {
                    "mainnet": {
                        "api_url": "https://api.hyperliquid.xyz",
                        "ws_url": "wss://api.hyperliquid.xyz/ws",
                        "name": "Hyperliquid Mainnet"
                    },
                    "testnet": {
                        "api_url": "https://api.hyperliquid-testnet.xyz",
                        "ws_url": "wss://api.hyperliquid-testnet.xyz/ws",
                        "name": "Hyperliquid Testnet"
                    }
                },
                "account": {
                    "address": "0x0Cb7aa8dDd145c3e6d1c2e8c63A0dFf8D8990138"
                },
                "api_secrets": {
                    "mainnet": "",
                    "testnet": "0xd05c9314fbd68b22b5e0a1b4f0291bfffa82bad625dab18bc1aaee97281fcc08"
                },
                "database": {
                    "path": "database/trading_data.db"
                },
                "server": {
                    "host": "0.0.0.0",
                    "port": 8000,
                    "reload": True
                }
            }
        
        # Load credentials from credentials.yaml if it exists
        credentials_path = Path(__file__).parent.parent / "credentials.yaml"
        if credentials_path.exists():
            with open(credentials_path, 'r') as f:
                credentials = yaml.safe_load(f)
                print(f"[Config] Loaded credentials from: {credentials_path}")
                
                # Override config with credentials
                if 'account_address' in credentials:
                    self._config['account']['address'] = credentials['account_address']
                
                if 'api_secrets' in credentials:
                    if 'mainnet' in credentials['api_secrets'] and credentials['api_secrets']['mainnet']:
                        self._config['api_secrets']['mainnet'] = credentials['api_secrets']['mainnet']
                    if 'testnet' in credentials['api_secrets'] and credentials['api_secrets']['testnet']:
                        self._config['api_secrets']['testnet'] = credentials['api_secrets']['testnet']
                
                if 'settings' in credentials and 'default_network' in credentials['settings']:
                    self._config['default_network'] = credentials['settings']['default_network']
        
        # Load network from environment variable or use default from config
        env_network = os.getenv("HYPERLIQUID_NETWORK", self._config["default_network"]).lower()
        if env_network in ["mainnet", "testnet"]:
            self.network = Network(env_network)
        else:
            print(f"[Config] Warning: Unknown network '{env_network}', defaulting to testnet")
            self.network = Network.TESTNET
        
        # Load account address from environment or config
        self.account_address = os.getenv(
            "HYPERLIQUID_ACCOUNT_ADDRESS", 
            self._config["account"]["address"]
        )
        
        # Load API secrets from environment variables (override config)
        self.mainnet_api_secret = os.getenv(
            "HYPERLIQUID_MAINNET_API_SECRET", 
            self._config["api_secrets"].get("mainnet", "")
        )
        self.testnet_api_secret = os.getenv(
            "HYPERLIQUID_TESTNET_API_SECRET", 
            self._config["api_secrets"].get("testnet", "")
        )
        
        self._initialized = True
        
        print(f"[Config] Initialized with network: {self.network.value}")
        print(f"[Config] Account address: {self.account_address}")
        if config_path.exists():
            print(f"[Config] Loaded configuration from: {config_path}")
        
        # Check if API secrets are configured
        if self.network == Network.MAINNET and not self.mainnet_api_secret:
            print("[Config] WARNING: No mainnet API secret configured!")
        elif self.network == Network.TESTNET and not self.testnet_api_secret:
            print("[Config] WARNING: No testnet API secret configured!")
    
    @property
    def is_testnet(self) -> bool:
        """Check if currently using testnet."""
        return self.network == Network.TESTNET
    
    @property
    def is_mainnet(self) -> bool:
        """Check if currently using mainnet."""
        return self.network == Network.MAINNET
    
    @property
    def api_secret(self) -> str:
        """Get the appropriate API secret for the current network."""
        if self.is_testnet:
            return self.testnet_api_secret
        return self.mainnet_api_secret
    
    @property
    def network_name(self) -> str:
        """Get the current network name as a string."""
        return self.network.value
    
    @property
    def api_url(self) -> str:
        """Get the API URL for the current network."""
        return self._config["networks"][self.network_name]["api_url"]
    
    @property
    def ws_url(self) -> str:
        """Get the WebSocket URL for the current network."""
        return self._config["networks"][self.network_name]["ws_url"]
    
    @property
    def network_display_name(self) -> str:
        """Get the display name for the current network."""
        return self._config["networks"][self.network_name]["name"]
    
    @property
    def database_path(self) -> str:
        """Get the database path."""
        return self._config["database"]["path"]
    
    @property
    def server_config(self) -> Dict[str, Any]:
        """Get server configuration."""
        return self._config["server"]
    
    def set_network(self, network: str):
        """
        Set the network at runtime.
        
        Args:
            network: Either "mainnet" or "testnet"
        """
        network_lower = network.lower()
        if network_lower == "mainnet":
            self.network = Network.MAINNET
            print(f"[Config] Switched to MAINNET ({self.api_url})")
        elif network_lower == "testnet":
            self.network = Network.TESTNET
            print(f"[Config] Switched to TESTNET ({self.api_url})")
        else:
            raise ValueError(f"Invalid network: {network}. Must be 'mainnet' or 'testnet'")
    
    def get_hyperliquid_client_params(self) -> dict:
        """Get parameters for initializing HyperClient."""
        return {
            "account_address": self.account_address,
            "api_secret": self.api_secret,
            "testnet": self.is_testnet
        }
    
    def reload(self):
        """Reload configuration from file."""
        self._initialized = False
        self.__init__()

# Global config instance
config = Config() 