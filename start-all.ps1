# E-Commerce Intelligence Platform - PowerShell Startup Script
# Starts both backend and frontend servers

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "E-Commerce Intelligence Platform" -ForegroundColor Cyan
Write-Host "Starting Backend and Frontend Servers..." -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if frontend dependencies are installed
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "ERROR: Frontend dependencies not found!" -ForegroundColor Red
    Write-Host "Please run: cd frontend && npm install" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "WARNING: Virtual environment not found!" -ForegroundColor Yellow
    Write-Host "Please run: python -m venv venv" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Start Backend Server
Write-Host "Starting Backend Server (Port 8000)..." -ForegroundColor Green
$backendJob = Start-Job -ScriptBlock {
    param($workDir)
    Set-Location $workDir
    
    # Activate virtual environment and start backend
    & "$workDir\venv\Scripts\Activate.ps1"
    python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
} -ArgumentList $PWD

# Wait for backend to initialize
Write-Host "Waiting for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check if backend started successfully
$backendRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        $backendRunning = $true
        Write-Host "✓ Backend is running!" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠ Backend may still be starting..." -ForegroundColor Yellow
}

Write-Host ""

# Start Frontend Server
Write-Host "Starting Frontend Server (Port 5174)..." -ForegroundColor Green
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Servers Starting:" -ForegroundColor Cyan
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "  Frontend: http://localhost:5174" -ForegroundColor White
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop all servers" -ForegroundColor Yellow
Write-Host ""

# Start frontend in current terminal (so we can see output)
Set-Location frontend
npm run dev

# Cleanup: Stop backend when frontend stops
Write-Host ""
Write-Host "Stopping backend server..." -ForegroundColor Yellow
Stop-Job -Job $backendJob
Remove-Job -Job $backendJob
Write-Host "All servers stopped." -ForegroundColor Green
