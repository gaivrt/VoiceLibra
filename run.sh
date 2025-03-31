#!/bin/bash

# VoiceLibra Project Runner
# This script initializes and runs the VoiceLibra project

echo "Starting VoiceLibra setup..."

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Clear log file
echo "" > debug.log
echo "Log file cleared."

# Check for required directories
if [ ! -d "data" ]; then
    mkdir data
    echo "Created data directory."
fi

# Run the main application
echo "Starting VoiceLibra application..."
python main.py

# Display log output
echo "Execution completed. Log file contents:"
echo "-----------------------------------"
tail -n 20 debug.log
echo "-----------------------------------"

# Deactivate virtual environment
deactivate

echo "VoiceLibra execution finished."