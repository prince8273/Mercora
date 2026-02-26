#!/bin/bash
# Setup script for Unix-like systems (Linux, macOS)

echo "Setting up E-commerce Intelligence Agent..."

# Create virtual environment
echo "Creating virtual environment..."
python -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Setup complete!"
echo "To activate the virtual environment, run: source venv/bin/activate"
echo "To start the application, run: python src/main.py"
