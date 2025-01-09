#!/usr/bin/env python3

try:
    print("=== Testing module imports ===")
    from app.main import app
    print("Module imports successful")
    print("FastAPI app loaded successfully")
except Exception as e:
    print(f"Error loading modules: {e}")
