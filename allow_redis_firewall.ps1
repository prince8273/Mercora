# PowerShell script to allow Redis traffic through Windows Firewall
# Run as Administrator

Write-Host "Adding Windows Firewall rule for WSL Redis..." -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Right-click PowerShell and select 'Run as Administrator', then run this script again." -ForegroundColor Yellow
    exit 1
}

# Get WSL IP address
Write-Host "Getting WSL IP address..." -ForegroundColor Yellow
$wslIP = wsl hostname -I
$wslIP = $wslIP.Trim()
Write-Host "WSL IP: $wslIP" -ForegroundColor Green
Write-Host ""

# Remove existing rule if it exists
Write-Host "Removing old firewall rule (if exists)..." -ForegroundColor Yellow
Remove-NetFirewallRule -DisplayName "WSL Redis Access" -ErrorAction SilentlyContinue

# Add inbound rule for Redis port 6379
Write-Host "Adding new firewall rule..." -ForegroundColor Yellow
New-NetFirewallRule `
    -DisplayName "WSL Redis Access" `
    -Direction Inbound `
    -LocalPort 6379 `
    -Protocol TCP `
    -Action Allow `
    -Profile Any `
    -Description "Allow Windows to connect to Redis running in WSL"

Write-Host ""
Write-Host "✅ Firewall rule added successfully!" -ForegroundColor Green
Write-Host ""

# Test the connection
Write-Host "Testing Redis connection..." -ForegroundColor Yellow
$testResult = Test-NetConnection -ComputerName $wslIP -Port 6379 -WarningAction SilentlyContinue

if ($testResult.TcpTestSucceeded) {
    Write-Host "✅ Redis connection successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Redis is now accessible at: redis://$wslIP:6379/0" -ForegroundColor Cyan
} else {
    Write-Host "⚠️  Connection test failed" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Additional steps to try:" -ForegroundColor Yellow
    Write-Host "1. Restart WSL: wsl --shutdown" -ForegroundColor White
    Write-Host "2. Start WSL again and run: sudo service redis-server restart" -ForegroundColor White
    Write-Host "3. Check if Redis is listening: wsl netstat -tlnp | grep 6379" -ForegroundColor White
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
