# Network Toggle Feature

This document explains how to use the mainnet/testnet toggle feature in the Hyperliquid Trading Assistant.

## Overview

The application now supports switching between Hyperliquid's mainnet and testnet environments. This allows you to:
- Test strategies on testnet without risking real funds
- Keep separate trading histories for mainnet and testnet
- Switch between networks without restarting the application

## Database Structure

The database now maintains separate records for each network:
- All trades, positions, and open orders are tagged with a `network` field
- Historical data is preserved when switching networks
- Each network maintains its own trading history and positions

## Running the Application

### Command Line Options

```bash
# Run on testnet (default)
python run_backend.py

# Run on testnet explicitly
python run_backend.py --testnet

# Run on mainnet
python run_backend.py --mainnet

# Custom port
python run_backend.py --port 8080
```

### Environment Variables

You can also control the network via environment variables:

```bash
# Set default network
export HYPERLIQUID_NETWORK=mainnet  # or testnet

# Set account address (used for both networks)
export HYPERLIQUID_ACCOUNT_ADDRESS=0xYourAddress

# Set API secrets for each network
export HYPERLIQUID_MAINNET_API_SECRET=0xYourMainnetSecret
export HYPERLIQUID_TESTNET_API_SECRET=0xYourTestnetSecret
```

## Frontend Network Indicator

The frontend displays a network indicator in the top-right corner:
- **Orange dot**: Testnet
- **Green dot**: Mainnet

Click the indicator to switch between networks. The page will reload to ensure all components use the new network.

## API Endpoints

### Get Current Network
```
GET /api/network
```

Response:
```json
{
  "network": "testnet",
  "is_testnet": true,
  "is_mainnet": false
}
```

### Switch Network
```
POST /api/network
Content-Type: application/json

"mainnet"  // or "testnet"
```

Response:
```json
{
  "success": true,
  "network": "mainnet",
  "message": "Switched to mainnet"
}
```

## Database Migration

When you first run the application after this update, it will automatically migrate your existing database:
- Existing data will be tagged as `testnet` data
- New tables with network support will be created
- Old tables will be replaced

To manually run the migration:
```bash
python migrate_database.py
```

## Configuration Module

The `src/config.py` module manages all network-related configuration:

```python
from src.config import config

# Get current network
print(config.network_name)  # "mainnet" or "testnet"
print(config.is_testnet)    # True/False
print(config.is_mainnet)    # True/False

# Get API credentials for current network
print(config.api_secret)     # Returns appropriate secret
print(config.account_address)

# Get HyperClient initialization parameters
client_params = config.get_hyperliquid_client_params()
# Returns: {"account_address": "...", "api_secret": "...", "testnet": True/False}
```

## Important Notes

1. **Data Separation**: Mainnet and testnet data are completely separate. Trades on one network won't appear when viewing the other.

2. **API Secrets**: Make sure you have the correct API secret for each network. Testnet and mainnet use different secrets.

3. **Default Network**: The application defaults to testnet for safety. Always double-check which network you're on before trading.

4. **WebSocket Connections**: Order book WebSocket connections will reconnect when switching networks.

5. **Price Data**: Price charts and market data come from the selected network. Testnet prices may differ from mainnet.

## Security Considerations

- Never commit your mainnet API secret to version control
- Use environment variables for sensitive configuration
- Always verify you're on the correct network before placing trades
- Consider using read-only API keys when possible

## Troubleshooting

### Migration Issues
If the database migration fails:
1. Backup your existing database: `cp database/trading_data.db database/trading_data.db.backup`
2. Delete the database: `rm database/trading_data.db`
3. Restart the application to create a fresh database

### Network Switch Fails
If switching networks fails:
1. Check the backend logs for errors
2. Ensure both API secrets are correctly configured
3. Try restarting the backend server

### Data Not Showing After Switch
Remember that each network has separate data. If you don't see expected data after switching:
1. Verify you're on the correct network
2. Check that the data was created on that network
3. Use the database query tools to verify data exists 