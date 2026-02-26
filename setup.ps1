# Setup script for Windows PowerShell

Write-Host "Setting up E-commerce Intelligence Agent..." -ForegroundColor Green

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
python -m venv venv

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "To activate the virtual environment, run: .\venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host "To start the application, run: python src/main.py" -ForegroundColor Cyan
