#!/bin/bash

# Hyperliquid Trading Assistant - Start Script

echo "🚀 Starting Hyperliquid Trading Assistant..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Check if credentials.yaml exists
if [ ! -f "credentials.yaml" ]; then
    echo "❌ credentials.yaml not found. Please run ./setup.sh and configure your API keys."
    exit 1
fi

# Check if OpenAI API key is set
# Note: Commented out since OpenAI API key is now hardcoded in src/reasoning/llm_client.py
# if [ -z "$OPENAI_API_KEY" ]; then
#     echo "⚠️  WARNING: OPENAI_API_KEY not set. LLM/chat features will not work."
#     echo "   Set it with: export OPENAI_API_KEY='sk-your-key-here'"
#     echo ""
# fi

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit
}

# Set up trap to cleanup on script exit
trap cleanup EXIT INT TERM

# Start backend
echo "🔧 Starting backend server..."
source venv/bin/activate
python run_backend.py --testnet &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend
echo "🎨 Starting frontend server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait a moment for services to start
sleep 3

echo ""
echo "✅ Application started successfully!"
echo ""
echo "🌐 Frontend: http://localhost:5170"
echo "🔧 Backend:  http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Keep script running
wait 