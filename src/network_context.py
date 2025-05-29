"""
Network context management for request-scoped network selection.
This allows different parts of the application to operate on different networks simultaneously.
"""

from contextlib import contextmanager
from typing import Optional
import threading
from src.config import config, Network

# Thread-local storage for network context
_network_context = threading.local()

@contextmanager
def network_context(network: Optional[str] = None):
    """
    Context manager for temporarily setting the network for the current thread.
    
    Usage:
        with network_context("mainnet"):
            # All operations in this block will use mainnet
            client = get_hyperliquid_client()
            trades = get_all_trades()  # Will get mainnet trades
    
    Args:
        network: "mainnet" or "testnet". If None, uses the global config network.
    """
    # Save current network
    previous_network = getattr(_network_context, 'network', None)
    
    try:
        # Set new network for this thread
        if network:
            _network_context.network = network
        else:
            _network_context.network = config.network_name
        
        yield _network_context.network
    finally:
        # Restore previous network
        if previous_network:
            _network_context.network = previous_network
        else:
            if hasattr(_network_context, 'network'):
                delattr(_network_context, 'network')

def get_current_network() -> str:
    """
    Get the current network for this thread.
    Falls back to global config if no thread-local network is set.
    """
    return getattr(_network_context, 'network', config.network_name)

def is_testnet() -> bool:
    """Check if current context is using testnet."""
    return get_current_network() == "testnet"

def is_mainnet() -> bool:
    """Check if current context is using mainnet."""
    return get_current_network() == "mainnet"

def get_network_config() -> dict:
    """Get configuration for the current network."""
    network = get_current_network()
    return config._config["networks"][network]

def get_api_url() -> str:
    """Get API URL for the current network context."""
    return get_network_config()["api_url"]

def get_ws_url() -> str:
    """Get WebSocket URL for the current network context."""
    return get_network_config()["ws_url"]

def get_api_secret() -> str:
    """Get API secret for the current network context."""
    network = get_current_network()
    if network == "mainnet":
        return config.mainnet_api_secret
    return config.testnet_api_secret

def get_hyperliquid_client_params() -> dict:
    """Get parameters for initializing HyperClient in current context."""
    return {
        "account_address": config.account_address,
        "api_secret": get_api_secret(),
        "testnet": is_testnet()
    } 