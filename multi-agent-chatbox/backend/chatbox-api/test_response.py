import json
import sys

def format_conversation_response(json_str):
    try:
        data = json.loads(json_str)
        print("\nConversation Details:")
        print(f"ID: {data.get('conversation_id')}")
        print(f"Topic: {data.get('topic')}")
        print(f"Current Round: {data.get('current_round')}")
        print(f"Max Rounds: {data.get('max_rounds')}")
        print("\nAgents and Personalities:")
        agent_personalities = data.get('agent_personalities', {})
        for agent in data.get('agents', []):
            personality = agent_personalities.get(agent, "Unknown")
            print(f"- {agent}: {personality}")
        
        if 'messages' in data:
            print("\nMessages:")
            for msg in data['messages']:
                print(f"{msg['agent']}: {msg['content']}")
        
        return data.get('conversation_id')
    except json.JSONDecodeError:
        print("Error: Invalid JSON response")
        return None

if __name__ == '__main__':
    json_str = sys.stdin.read()
    format_conversation_response(json_str)
