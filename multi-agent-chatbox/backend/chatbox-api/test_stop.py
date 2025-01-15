import requests
import time
import sys

def test_stop_conversation():
    # Create a conversation
    response = requests.post(
        "http://localhost:8000/api/conversations",
        json={
            "agent_count": 3,
            "topic": "Testing conversation stopping",
            "round_count": 5
        }
    )
    data = response.json()
    conversation_id = data["conversation_id"]
    print(f"\nCreated conversation: {conversation_id}")
    
    # Wait for some messages
    time.sleep(10)
    
    # Get conversation state before stopping
    response = requests.get(f"http://localhost:8000/api/conversations/{conversation_id}")
    before_stop = response.json()
    print("\nBefore stopping:")
    print(f"Round: {before_stop['current_round']}")
    print(f"Messages: {len(before_stop['messages'])}")
    print(f"Is auto playing: {before_stop.get('is_auto_playing', False)}")
    
    # Stop the conversation
    response = requests.post(f"http://localhost:8000/api/conversations/{conversation_id}/stop")
    print("\nStopped conversation:", response.json())
    
    # Wait a moment for the stop to take effect
    time.sleep(2)
    
    # Get final state
    response = requests.get(f"http://localhost:8000/api/conversations/{conversation_id}")
    after_stop = response.json()
    print("\nAfter stopping:")
    print(f"Round: {after_stop['current_round']}")
    print(f"Messages: {len(after_stop['messages'])}")
    print(f"Is auto playing: {after_stop.get('is_auto_playing', False)}")
    print(f"Stopped: {after_stop.get('stopped', False)}")
    
    # Print all messages
    print("\nFull conversation:")
    for msg in after_stop['messages']:
        print(f"{msg['agent']}: {msg['content']}")

if __name__ == "__main__":
    test_stop_conversation()
