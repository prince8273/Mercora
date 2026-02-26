# Setup port forwarding from Windows localhost to WSL Redis
# Run as Administrator

Write-Host "Setting up port forwarding for Redis..." -ForegroundColor Cyan

# Get WSL IP
$wslIP = (wsl hostname -I).Trim()
Write-Host "WSL IP: $wslIP" -ForegroundColor Green

# Remove existing port proxy if exists
Write-Host "Removing old port proxy..." -ForegroundColor Yellow
netsh interface portproxy delete v4tov4 listenport=6379 listenaddress=127.0.0.1 | Out-Null

# Add port proxy from localhost:6379 to WSL:6379
Write-Host "Adding port proxy: localhost:6379 -> $wslIP:6379" -ForegroundColor Yellow
netsh interface portproxy add v4tov4 listenport=6379 listenaddress=127.0.0.1 connectport=6379 connectaddress=$wslIP

# Show current port proxies
Write-Host ""
Write-Host "Current port proxies:" -ForegroundColor Cyan
netsh interface portproxy show all

Write-Host ""
Write-Host "✅ Port forwarding configured!" -ForegroundColor Green
Write-Host ""
Write-Host "Now update your .env file:" -ForegroundColor Yellow
Write-Host "  REDIS_URL=redis://localhost:6379/0" -ForegroundColor White
Write-Host ""
