#!/bin/bash
# Configure Redis in WSL to accept connections from Windows
# Run this in your WSL terminal

# Stop Redis
redis-cli shutdown

# Start Redis bound to all interfaces (allows Windows to connect)
redis-server --bind 0.0.0.0 --protected-mode no --daemonize yes

# Verify it's running
redis-cli ping

echo "Redis is now accessible from Windows at localhost:6379"
