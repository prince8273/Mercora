#!/bin/bash
# Fix Redis configuration in WSL to accept connections from Windows

echo "Checking Redis configuration..."

# Check if Redis is running
if ! pgrep -x "redis-server" > /dev/null; then
    echo "Redis is not running. Starting Redis..."
    sudo service redis-server start
fi

# Get WSL IP
WSL_IP=$(hostname -I | awk '{print $1}')
echo "WSL IP: $WSL_IP"

# Backup Redis config
sudo cp /etc/redis/redis.conf /etc/redis/redis.conf.backup

# Configure Redis to bind to WSL IP
echo "Configuring Redis to accept connections from Windows..."
sudo sed -i "s/^bind 127.0.0.1 ::1/bind 127.0.0.1 $WSL_IP/" /etc/redis/redis.conf

# Disable protected mode for local network
sudo sed -i 's/^protected-mode yes/protected-mode no/' /etc/redis/redis.conf

# Restart Redis
echo "Restarting Redis..."
sudo service redis-server restart

# Wait for Redis to start
sleep 2

# Test connection
echo "Testing Redis connection..."
redis-cli -h $WSL_IP ping

echo ""
echo "Redis configuration complete!"
echo "Redis is now accessible at: redis://$WSL_IP:6379/0"
echo ""
echo "Test from Windows PowerShell with:"
echo "  Test-NetConnection -ComputerName $WSL_IP -Port 6379"
