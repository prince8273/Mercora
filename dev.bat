@echo off
REM Quick dev start - Both servers in same terminal

echo Starting E-Commerce Intelligence Platform...
echo.

REM Start backend in background
start /b python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

REM Wait 3 seconds
timeout /t 3 /nobreak >nul

REM Start frontend (this will show output)
cd frontend && npm run dev -- --port 3000
