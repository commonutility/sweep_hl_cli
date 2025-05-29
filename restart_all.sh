#!/bin/bash

echo "🔄 Restarting Hyperliquid Trading CLI..."
echo ""

# Kill any existing processes
echo "📍 Stopping existing processes..."
pkill -f "python.*main.py" 2>/dev/null
pkill -f "npm.*dev" 2>/dev/null
pkill -f "vite" 2>/dev/null

# Kill any process using port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null

# Wait a moment for processes to stop
sleep 2

# Clear the database (optional - comment out if you want to keep data)
echo "🗑️  Clearing database..."
rm -f trading_data.db
echo "   Database cleared."

# Start backend
echo ""
echo "🚀 Starting backend on mainnet..."
cd backend
HYPERLIQUID_NETWORK=mainnet python main.py &
BACKEND_PID=$!
echo "   Backend started with PID: $BACKEND_PID"

# Wait for backend to initialize
echo "   Waiting for backend to initialize..."
sleep 5

# Start frontend
echo ""
echo "🎨 Starting frontend..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!
echo "   Frontend started with PID: $FRONTEND_PID"

echo ""
echo "✅ All services started!"
echo ""
echo "📋 Service URLs:"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:5170"
echo ""
echo "🛑 To stop all services, run: pkill -f 'python.*main.py' && pkill -f 'npm.*dev'"

# Wait for Ctrl+C
wait 