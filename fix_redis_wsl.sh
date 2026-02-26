#!/bin/bash
# Fix Redis to accept connections from Windows
# Run this in WSL terminal

echo "Stopping Redis..."
redis-cli shutdown

echo "Starting Redis with proper configuration..."
redis-server --bind 0.0.0.0 --protected-mode no --daemonize yes

echo "Waiting for Redis to start..."
sleep 2

echo "Testing Redis..."
redis-cli ping

echo "Checking Redis configuration..."
redis-cli CONFIG GET bind

echo ""
echo "✅ Redis should now be accessible from Windows at 172.27.52.219:6379"
