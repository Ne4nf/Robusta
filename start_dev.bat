@echo off
echo 🚀 Starting ROBUSTA Bot - Development Mode (Port 8000)

echo.
echo 📋 Starting Backend (Port 8000)...
cd /d "%~dp0\backend"
start "Backend" cmd /k "D:\Robusta\robusta-bot\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo.
echo 📋 Starting Frontend (Port 3000)...
cd /d "%~dp0\frontend"
start "Frontend" cmd /k "npm start"

echo.
echo ✅ Services started:
echo - Backend: http://localhost:8000
echo - Frontend: http://localhost:3000
echo - API Docs: http://localhost:8000/docs

pause
