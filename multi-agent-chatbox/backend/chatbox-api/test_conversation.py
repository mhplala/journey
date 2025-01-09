import json
import sys
import time
import requests

def create_conversation(topic: str, agent_count: int, round_count: int) -> str:
    response = requests.post(
        "http://localhost:8000/api/conversations",
        json={
            "agent_count": agent_count,
            "topic": topic,
            "round_count": round_count
        }
    )
    data = response.json()
    print("\nCreated Conversation:")
    print(f"ID: {data['conversation_id']}")
    print(f"Topic: {data['topic']}")
    print(f"Rounds: {data['max_rounds']}")
    print("\nAgents and Personalities:")
    for agent in data['agents']:
        print(f"- {agent}: {data['agent_personalities'][agent]}")
    return data['conversation_id']

def monitor_conversation(conversation_id: str, check_interval: int = 5, max_checks: int = 6):
    for i in range(max_checks):
        print(f"\nChecking conversation status (attempt {i + 1})...")
        response = requests.get(f"http://localhost:8000/api/conversations/{conversation_id}")
        data = response.json()
        
        print(f"Current Round: {data['current_round']}")
        if 'messages' in data:
            print("\nMessages:")
            for msg in data['messages']:
                print(f"{msg['agent']}: {msg['content']}")
        
        if 'summary' in data and data['summary']:
            print("\nFinal Summary:")
            print(data['summary'])
            break
            
        time.sleep(check_interval)

if __name__ == "__main__":
    conv_id = create_conversation(
        topic="The future of artificial intelligence",
        agent_count=3,
        round_count=3
    )
    monitor_conversation(conv_id)
