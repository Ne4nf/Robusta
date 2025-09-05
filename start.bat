@echo off
echo 🚀 Starting ROBUSTA Bot - React + FastAPI

echo.
echo 📋 Checking requirements...

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.12+
    pause
    exit /b 1
)

:: Check Node.js  
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found. Please install Node.js 18+
    pause
    exit /b 1
)

echo ✅ Python and Node.js found

echo.
echo 🔧 Setting up Python environment...
if not exist ".venv" (
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo 📦 Installing Python dependencies...
pip install -r requirements.txt

echo.
echo 📦 Installing Node.js dependencies...
cd frontend
call npm install
cd ..

echo.
echo 🌐 Starting services...
echo 📍 Backend: http://localhost:80
echo 📍 Frontend: http://localhost:3000

echo.
echo ⚡ Starting Backend (FastAPI)...
start cmd /k "cd backend && call ..\.venv\Scripts\activate.bat && python main.py"

timeout /t 3 /nobreak >nul

echo ⚡ Starting Frontend (React)...
start cmd /k "cd frontend && npm start"

echo.
echo 🎉 ROBUSTA Bot is starting!
echo 📖 Check the opened terminal windows for status
echo 🌐 Access at: http://localhost:3000
echo.
pause
