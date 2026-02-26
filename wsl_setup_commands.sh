#!/bin/bash
# WSL Python 3.11 Setup Commands
# Run these commands in your WSL terminal

# Add deadsnakes PPA for Python 3.11
sudo apt update
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# Install Python 3.11 and required packages
sudo apt install python3.11 python3.11-venv python3.11-dev -y

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Verify installation
python --version
which python

echo "Setup complete! Redis is already running."
echo "You can now run: pytest tests/integration/ -v"
