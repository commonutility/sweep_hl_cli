# Setting Up Hyperliquid Credentials

This guide will help you set up your Hyperliquid API credentials for both testnet and mainnet.

## Quick Start

1. Copy the credentials template:
   ```bash
   cp credentials.yaml.template credentials.yaml
   ```

2. Edit `credentials.yaml` and add your credentials
3. Start the application

## Getting Your API Credentials

### Testnet Credentials

1. Visit [Hyperliquid Testnet](https://testnet.hyperliquid.xyz)
2. Connect your wallet (MetaMask, WalletConnect, etc.)
3. Click on your address in the top right corner
4. Navigate to the "API Wallet" section
5. Click "Generate API Key" or copy your existing key
6. Copy the private key (starts with `0x`)

### Mainnet Credentials

⚠️ **WARNING**: Mainnet uses real funds. Be extremely careful with your mainnet API key!

1. Visit [Hyperliquid Mainnet](https://app.hyperliquid.xyz)
2. Connect your wallet (MetaMask, WalletConnect, etc.)
3. Click on your address in the top right corner
4. Navigate to the "API Wallet" section
5. Click "Generate API Key" or copy your existing key
6. Copy the private key (starts with `0x`)

## Configuration Options

### Using credentials.yaml (Recommended)

Edit the `credentials.yaml` file:

```yaml
account_address: "0xYourWalletAddress"

api_secrets:
  mainnet: "0xYourMainnetAPISecret"
  testnet: "0xYourTestnetAPISecret"

settings:
  default_network: "testnet"  # Start on testnet by default
```

### Using Environment Variables

You can also use environment variables:

```bash
# Set account address
export HYPERLIQUID_ACCOUNT_ADDRESS="0xYourWalletAddress"

# Set API secrets
export HYPERLIQUID_MAINNET_API_SECRET="0xYourMainnetSecret"
export HYPERLIQUID_TESTNET_API_SECRET="0xYourTestnetSecret"

# Set default network
export HYPERLIQUID_NETWORK="testnet"
```

### Priority Order

The configuration is loaded in this order (later overrides earlier):
1. Default values in `config.yaml`
2. Values from `credentials.yaml` (if exists)
3. Environment variables

## Security Best Practices

1. **Never commit credentials.yaml to version control**
   - The file is already in `.gitignore`
   - Double-check before committing

2. **Use different API keys for different purposes**
   - Consider having read-only keys for monitoring
   - Use separate keys for trading bots

3. **Limit API key permissions**
   - Only grant necessary permissions
   - Regularly rotate keys

4. **Start with testnet**
   - Always test strategies on testnet first
   - Testnet tokens have no real value

## Troubleshooting

### "Private key must be exactly 32 bytes long"
- Make sure your API secret starts with `0x`
- Ensure it's exactly 66 characters long (0x + 64 hex characters)
- Check for any extra spaces or newlines

### "502 Bad Gateway" on Testnet
- Testnet may be temporarily down
- Check status at https://status.hyperliquid.xyz
- You can use mainnet for testing (with caution!)

### "Authentication failed"
- Verify your API secret is correct
- Make sure you're using the right secret for the network
- Check that your wallet address matches

## Example credentials.yaml

Here's a complete example with the default testnet credentials:

```yaml
account_address: "0x0Cb7aa8dDd145c3e6d1c2e8c63A0dFf8D8990138"

api_secrets:
  mainnet: ""  # Add your mainnet secret here
  testnet: "0xd05c9314fbd68b22b5e0a1b4f0291bfffa82bad625dab18bc1aaee97281fcc08"

settings:
  default_network: "testnet"
```

## Next Steps

After setting up your credentials:

1. Start the backend:
   ```bash
   python run_backend.py --testnet  # or --mainnet
   ```

2. Start the frontend:
   ```bash
   cd frontend && npm run dev
   ```

3. Visit http://localhost:5170 and start trading! 