#!/bin/bash

# AI Agent UI Startup Script for Linux/Mac

echo ""
echo "======================================================================"
echo "                    AI Agent Personality Builder"
echo "======================================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.7+ and try again"
    exit 1
fi

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Installing required dependencies..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies"
        exit 1
    fi
fi

echo "Starting AI Agent Web UI Server..."
echo ""
echo "🚀 Opening http://localhost:5000 in your browser..."
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "======================================================================"
echo ""

# Open browser (platform-specific)
if command -v open &> /dev/null; then
    # macOS
    open "http://localhost:5000"
elif command -v xdg-open &> /dev/null; then
    # Linux
    xdg-open "http://localhost:5000"
fi

# Start the server
python3 ui_server.py
