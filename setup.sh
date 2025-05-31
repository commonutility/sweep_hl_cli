#!/bin/bash

# Hyperliquid Trading Assistant - Setup Script

echo "🚀 Setting up Hyperliquid Trading Assistant..."
echo ""

# Check Python version
echo "📌 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
if [[ -z "$python_version" ]]; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi
echo "✅ Python $python_version found"

# Check Node.js version
echo "📌 Checking Node.js version..."
node_version=$(node --version 2>&1)
if [[ -z "$node_version" ]]; then
    echo "❌ Node.js is not installed. Please install Node.js 16 or higher."
    exit 1
fi
echo "✅ Node.js $node_version found"

# Create virtual environment
echo ""
echo "📦 Creating Python virtual environment..."
python3 -m venv venv
echo "✅ Virtual environment created"

# Activate virtual environment
echo "📌 Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
echo "✅ Python dependencies installed"

# Install frontend dependencies
echo ""
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..
echo "✅ Frontend dependencies installed"

# Create credentials file if it doesn't exist
echo ""
if [ ! -f credentials.yaml ]; then
    echo "📝 Creating credentials.yaml from template..."
    cp credentials.yaml.template credentials.yaml
    echo "✅ credentials.yaml created"
    echo ""
    echo "⚠️  IMPORTANT: Edit credentials.yaml with your API keys before running the application!"
else
    echo "✅ credentials.yaml already exists"
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env from example..."
    cp env.example .env
    echo "✅ .env created"
    echo ""
    echo "⚠️  OPTIONAL: Edit .env if you want to override default settings"
else
    echo "✅ .env already exists"
fi

# Create database directory if it doesn't exist
echo ""
if [ ! -d database ]; then
    echo "📁 Creating database directory..."
    mkdir database
    echo "✅ Database directory created"
else
    echo "✅ Database directory already exists"
fi

echo ""
echo "✨ Setup complete! ✨"
echo ""
echo "Next steps:"
echo "1. Edit credentials.yaml with your Hyperliquid API keys"
echo "2. Run the application:"
echo "   - Backend: python run_backend.py --testnet"
echo "   - Frontend: cd frontend && npm run dev"
echo ""
echo "For detailed instructions, see README.md" 