import sys
import os
from pathlib import Path

def check_system():
    print("=== Python Path ===")
    for path in sys.path:
        print(path)
    
    print("\n=== Module Structure ===")
    app_dir = Path("app")
    for root, dirs, files in os.walk(app_dir):
        level = len(Path(root).relative_to(app_dir).parts)
        indent = "  " * level
        path = Path(root).relative_to(app_dir)
        print(f"{indent}{path}")
        for file in files:
            print(f"{indent}  {file}")

    print("\n=== Backend Logs ===")
    try:
        with open("/var/log/chatbox-api.log", "r") as f:
            print(f.read())
    except Exception as e:
        print(f"Error reading log file: {e}")

if __name__ == "__main__":
    check_system()
