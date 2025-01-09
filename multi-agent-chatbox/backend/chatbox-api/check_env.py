#!/usr/bin/env python3

import sys
import os

def check_environment():
    print("=== Python Environment Check ===")
    print("\nPython Path:")
    for path in sys.path:
        print(f"- {path}")
    
    print("\nModule Structure:")
    app_dir = os.path.join(os.path.dirname(__file__), "app")
    for root, dirs, files in os.walk(app_dir):
        level = root.replace(app_dir, "").count(os.sep)
        indent = " " * 4 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = " " * 4 * (level + 1)
        for f in files:
            print(f"{subindent}{f}")

if __name__ == "__main__":
    try:
        print("=== Testing module imports ===")
        from app.main import app
        print("Module imports successful")
        print("FastAPI app loaded successfully")
        print("\nChecking environment details:")
        check_environment()
    except Exception as e:
        print(f"Error: {e}")
        print("\nChecking environment details despite error:")
        check_environment()
