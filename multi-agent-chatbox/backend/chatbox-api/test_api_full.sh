#!/bin/bash
set -e

echo "Killing existing uvicorn processes..."
pkill -f uvicorn || true

echo "Starting backend service..."
cd /root/chatbox-api
export PATH=/root/.local/bin:$PATH
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug > /var/log/backend.log 2>&1 &

echo "Waiting for service to start..."
sleep 5

echo "Testing health endpoint..."
curl -v http://localhost:8000/healthz

echo -e "\nTesting conversation creation..."
CONV_RESPONSE=$(curl -v -X POST -H "Content-Type: application/json" -d '{"agent_count": 3}' http://localhost:8000/api/conversations)
CONV_ID=$(echo $CONV_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['conversation_id'])")

echo -e "\nTesting full 10-round conversation..."
for i in {1..10}; do
  echo -e "\nStarting round $i..."
  for agent in $(seq 1 3); do
    echo -e "\nAgent $agent sending message in round $i..."
    curl -v -X POST -H "Content-Type: application/json" -d "{\"conversation_id\": \"$CONV_ID\", \"agent\": \"Agent $agent\", \"message\": \"This is a test message from Agent $agent in round $i\"}" http://localhost:8000/api/chat
    sleep 2
  done
done

echo -e "\nGetting final conversation state with summary..."
curl -v http://localhost:8000/api/conversations/$CONV_ID
