import json
import sys
from datetime import datetime

def format_topics(json_str):
    try:
        data = json.loads(json_str)
        print("\nTopics in chronological order:")
        topics = sorted(
            data.get('topics', []),
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )
        
        for i, topic in enumerate(topics, 1):
            print(f"\n{i}. Topic: {topic.get('text', 'N/A')}")
            print(f"   Time: {topic.get('timestamp', 'N/A')}")
            print(f"   Agents: {len(topic.get('agents', []))}")
            print(f"   Messages: {len(topic.get('messages', []))}")
            print(f"   Summary: {'Present' if topic.get('summary') else 'None'}")
            
        if not topics:
            print("\nNo topics found in the system.")
            
    except json.JSONDecodeError:
        print("Error: Invalid JSON response")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    try:
        json_str = sys.stdin.read()
        format_topics(json_str)
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)
