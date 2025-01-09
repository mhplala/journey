#!/bin/bash

# Install Python dependencies system-wide
sudo pip3 install fastapi uvicorn python-dotenv requests

# Kill any existing uvicorn processes
sudo pkill -f "uvicorn app.main:app"

# Start the FastAPI server
cd /home/ubuntu/multi-agent-chatbox/backend/chatbox-api
sudo nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /var/log/chatbox-api.log 2>&1 &

# Wait for server to start
sleep 5

# Check if server is running
if pgrep -f "uvicorn app.main:app" > /dev/null; then
    echo "FastAPI server started successfully"
else
    echo "Failed to start FastAPI server"
    exit 1
fi
