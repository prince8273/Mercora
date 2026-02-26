# Single command to start both servers in same terminal
# Backend runs in background, frontend output is shown

Write-Host "Starting E-Commerce Intelligence Platform..." -ForegroundColor Cyan
Write-Host ""

# Start backend in background
Write-Host "Starting Backend (Port 8000)..." -ForegroundColor Green
$backend = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload" -PassThru -WindowStyle Minimized

# Wait for backend
Start-Sleep -Seconds 3

# Start frontend in current terminal
Write-Host "Starting Frontend (Port 3000)..." -ForegroundColor Green
Write-Host ""
Set-Location frontend
npm run dev -- --port 3000
