@echo off
REM E-Commerce Intelligence Platform - Start Both Servers
REM Runs backend and frontend concurrently in the same window

echo ==========================================
echo E-Commerce Intelligence Platform
echo Starting Backend and Frontend Servers...
echo ==========================================
echo.

REM Check if frontend dependencies are installed
if not exist "frontend\node_modules\" (
    echo ERROR: Frontend dependencies not found!
    echo Please run: cd frontend ^&^& npm install
    pause
    exit /b 1
)

REM Use concurrently package or start both with start /b
echo Starting Backend Server (Port 8000)...
start /b cmd /c "set PYTHONPATH=%CD%\venv\Lib\site-packages;%PYTHONPATH% && python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload 2>&1"

REM Wait for backend to initialize
timeout /t 3 /nobreak >nul

echo Starting Frontend Server (Port 3000)...
cd frontend
npm run dev -- --port 3000
