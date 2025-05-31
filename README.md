# Hyperliquid Trading Assistant

A full-stack application for interacting with the Hyperliquid decentralized exchange, featuring a React frontend and FastAPI backend.

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** 
- **Node.js 16+** and npm
- **Git**

### Automatic Setup

#### macOS/Linux:
```bash
./setup.sh
```

#### Windows:
```batch
setup.bat
```

The setup script will:
- Check system requirements
- Create a Python virtual environment
- Install all dependencies
- Create configuration files from templates
- Set up the database directory

### Configure API Keys

Edit `credentials.yaml` with your Hyperliquid API keys (see [Getting API Credentials](#-getting-api-credentials) section below).

### Run the Application

#### macOS/Linux:
```bash
./start.sh
```

#### Windows:
```batch
start.bat
```

This will start both the backend and frontend servers. Visit http://localhost:5170 to use the application.

## 📋 Manual Setup

If you prefer to set up manually or the automatic setup fails:

### 1. Clone the repository
```bash
git clone <repository-url>
cd sweep_hl_cli
```

### 2. Python Backend Setup

Create and activate a virtual environment:
```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

Install Python dependencies:
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

### 3. Frontend Setup

Install Node.js dependencies:
```bash
cd frontend
npm install
cd ..
```

### 4. Configuration

#### Create credentials file:
```bash
cp credentials.yaml.template credentials.yaml
```

Edit `credentials.yaml` with your Hyperliquid API credentials:
```yaml
account_address: "0xYourWalletAddress"

api_secrets:
  mainnet: "0xYourMainnetAPISecret"  # Leave empty if only using testnet
  testnet: "0xYourTestnetAPISecret"

settings:
  default_network: "testnet"  # Start with testnet for safety
```

#### (Optional) Environment Variables:
```bash
cp env.example .env
```

Edit `.env` to override default settings if needed.

#### Set OpenAI API Key (Required for LLM features):

**Note: The OpenAI API key is currently hardcoded in the source code.**

Edit `src/reasoning/llm_client.py` line 20:
```python
# Replace this placeholder with your actual OpenAI API key:
api_key = "sk-REPLACE-WITH-YOUR-ACTUAL-OPENAI-API-KEY"
```

To get an OpenAI API key, visit: https://platform.openai.com/api-keys

## 🔑 Getting API Credentials

### Testnet (Recommended for testing)
1. Visit [Hyperliquid Testnet](https://testnet.hyperliquid.xyz)
2. Connect your wallet (MetaMask, etc.)
3. Click your address → "API Wallet" → "Generate API Key"
4. Copy the private key (starts with `0x`)

### Mainnet (Real funds - use with caution!)
1. Visit [Hyperliquid Mainnet](https://app.hyperliquid.xyz)
2. Follow the same process as testnet
3. **⚠️ WARNING**: Mainnet uses real funds. Keep your API key secure!

## ▶️ Running the Application

### Option 1: Use the Start Script (Recommended)

#### macOS/Linux:
```bash
./start.sh
```

#### Windows:
```batch
start.bat
```

### Option 2: Run Services Manually

#### Start the Backend Server

```bash
# Activate virtual environment first
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Run on testnet (recommended)
python run_backend.py --testnet

# Or run on mainnet (use with caution)
python run_backend.py --mainnet
```

The backend will start on `http://localhost:8000`

#### Start the Frontend Development Server

In a new terminal:
```bash
cd frontend
npm run dev
```

The frontend will start on `http://localhost:5170`

Visit `http://localhost:5170` in your browser to use the application.

## 📁 Project Structure

```
sweep_hl_cli/
├── backend/            # FastAPI backend server
├── frontend/           # React + Vite frontend
├── src/               # Core Python library code
├── database/          # SQLite database storage
├── credentials.yaml   # API credentials (DO NOT COMMIT)
├── config.yaml        # Application configuration
├── requirements.txt   # Python dependencies
├── setup.sh/bat       # One-time setup scripts
└── start.sh/bat       # Application start scripts
```

## 🔧 Common Issues

### "Private key must be exactly 32 bytes long"
- Ensure your API secret starts with `0x`
- Check it's exactly 66 characters (0x + 64 hex chars)
- Remove any spaces or newlines

### "502 Bad Gateway" on Testnet
- Testnet may be temporarily down
- Check status at https://status.hyperliquid.xyz

### "Module not found" errors
- Make sure you've activated the virtual environment
- Run `pip install -r requirements.txt` again

### Frontend connection issues
- Ensure backend is running first
- Check backend is on port 8000
- Check for CORS errors in browser console

### "No module named 'openai'"
- Install OpenAI package: `pip install openai`
- Make sure `OPENAI_API_KEY` environment variable is set

## 🛡️ Security Best Practices

1. **Never commit `credentials.yaml` or `.env` files**
2. Use testnet for development and testing
3. Keep API keys secure and rotate regularly
4. Use read-only keys when possible
5. Set appropriate API key permissions

## 📚 Additional Documentation

- `CREDENTIALS_SETUP.md` - Detailed credentials setup guide
- `NETWORK_TOGGLE_README.md` - Network switching documentation
- `UI_RENDERING_ARCHITECTURE.md` - Frontend architecture details
- `USER_SETUP_CHECKLIST.md` - Complete list of user-specific configurations

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review additional documentation files
3. Check Hyperliquid's official documentation
4. Open an issue in the repository

## ⚡ Quick Commands Reference

```bash
# First-time setup
./setup.sh              # macOS/Linux
setup.bat               # Windows

# Configure API keys
nano credentials.yaml   # or use your preferred editor

# Set OpenAI API key (required for LLM features)
# Edit src/reasoning/llm_client.py and replace the placeholder API key

# Run the application
./start.sh              # macOS/Linux (runs both services)
start.bat               # Windows (runs both services)

# Or run services individually
# Terminal 1 - Backend:
source venv/bin/activate
python run_backend.py --testnet

# Terminal 2 - Frontend:
cd frontend && npm run dev

# Access the application
open http://localhost:5170      # Frontend
open http://localhost:8000/docs # API documentation
``` 