# User Setup Checklist

This document lists all the user-specific configurations needed to run the Hyperliquid Trading Assistant.

## Required Configurations

### 1. Hyperliquid API Credentials

**File:** `credentials.yaml`

- **account_address**: Your Hyperliquid wallet address (same for both networks)
  - Default: `0x0Cb7aa8dDd145c3e6d1c2e8c63A0dFf8D8990138` (testnet demo account)
  - Replace with your actual wallet address

- **api_secrets.mainnet**: Your mainnet API secret key
  - Default: Empty (must be set for mainnet usage)
  - Get from: https://app.hyperliquid.xyz → API settings

- **api_secrets.testnet**: Your testnet API secret key
  - Default: `0xd05c9314fbd68b22b5e0a1b4f0291bfffa82bad625dab18bc1aaee97281fcc08` (public testnet key)
  - Get your own from: https://testnet.hyperliquid.xyz → API settings

### 2. OpenAI API Key (Required for LLM features)

**Option A - Environment Variable (Original Method):**
- Set via: `export OPENAI_API_KEY="sk-your-api-key-here"`
- Or add to `.env` file: `OPENAI_API_KEY=sk-your-api-key-here`

**Option B - Hardcoded (Current Implementation):**
- Edit `src/reasoning/llm_client.py` line 20
- Replace `"sk-REPLACE-WITH-YOUR-ACTUAL-OPENAI-API-KEY"` with your actual key
- Note: Be careful not to commit this change to version control

### 3. Optional Environment Variables

These can override values in `credentials.yaml` (currently commented out in code):

- `HYPERLIQUID_ACCOUNT_ADDRESS` - Override wallet address
- `HYPERLIQUID_MAINNET_API_SECRET` - Override mainnet API secret
- `HYPERLIQUID_TESTNET_API_SECRET` - Override testnet API secret
- `HYPERLIQUID_NETWORK` - Set default network (mainnet/testnet)

## Hardcoded Values Mode

The application is currently configured to use hardcoded values instead of environment variables. To modify credentials:

### Hyperliquid Settings
- Edit `credentials.yaml` for all Hyperliquid-related settings
- The values in `credentials.yaml` will be used directly (environment variables are ignored)

### OpenAI API Key
- Edit `src/reasoning/llm_client.py` line 20
- Replace the placeholder with your actual OpenAI API key

### Re-enabling Environment Variables
If you want to use environment variables instead:
1. Edit `src/config.py` - uncomment the `os.getenv()` lines and comment the hardcoded lines
2. Edit `src/reasoning/llm_client.py` - uncomment the `os.getenv()` line and remove the hardcoded line

## Default Values Location

The application uses a configuration hierarchy:
1. ~~**Environment variables** (highest priority)~~ *(Currently disabled)*
2. **credentials.yaml** file *(Currently primary source)*
3. **config.yaml** file
4. **Hardcoded defaults** in `src/config.py` (lowest priority)

The hardcoded defaults in `src/config.py` are:
- Account: `0x0Cb7aa8dDd145c3e6d1c2e8c63A0dFf8D8990138`
- Testnet Secret: `0xd05c9314fbd68b22b5e0a1b4f0291bfffa82bad625dab18bc1aaee97281fcc08`
- Mainnet Secret: Empty (must be provided)

## Security Notes

1. **Never commit** `credentials.yaml` or modified source files with real API keys
2. The default testnet credentials are public and safe for testing
3. For production/mainnet use, always use your own API keys
4. Keep your mainnet API secret secure - it can execute trades with real funds

## Quick Setup for New Users

1. Run setup script: `./setup.sh` or `setup.bat`
2. Edit `credentials.yaml`:
   - Replace `account_address` with your wallet address
   - Add your `mainnet` API secret (if using mainnet)
   - Optionally replace `testnet` secret with your own
3. Edit `src/reasoning/llm_client.py`:
   - Replace the OpenAI API key placeholder with your actual key
4. Run the application: `./start.sh` or `start.bat`

## Port Configuration

- Backend API: Port 8000
- Frontend Dev Server: Port 5170 (configured in `frontend/vite.config.js`)
- API Documentation: http://localhost:8000/docs 