#!/bin/bash

echo "🚀 Starting ROBUSTA Bot - React + FastAPI"

echo ""
echo "📋 Checking requirements..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.12+"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi

echo "✅ Python and Node.js found"

echo ""
echo "🔧 Setting up Python environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "📦 Installing Node.js dependencies..."
cd frontend
npm install
cd ..

echo ""
echo "🌐 Starting services..."
echo "📍 Backend: http://localhost:80"
echo "📍 Frontend: http://localhost:3000"

echo ""
echo "⚡ Starting Backend (FastAPI)..."
cd backend
uvicorn main:app --reload --host localhost --port 80 &
BACKEND_PID=$!
cd ..

sleep 3

echo "⚡ Starting Frontend (React)..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "🎉 ROBUSTA Bot is running!"
echo "📖 Backend PID: $BACKEND_PID"
echo "📖 Frontend PID: $FRONTEND_PID"
echo "🌐 Access at: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both services"

# Wait for user interrupt
wait
