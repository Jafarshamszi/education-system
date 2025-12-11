#!/usr/bin/env python3
import os
import sys
import subprocess

# Change to the correct directory
backend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(backend_dir)

# Add the backend directory to Python path
sys.path.insert(0, backend_dir)

print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path[0]}")

# Check if app module exists
if os.path.exists("app"):
    print("✅ App directory found")
    if os.path.exists("app/main_debug.py"):
        print("✅ App main_debug.py found")
    else:
        print("❌ App main_debug.py not found")
else:
    print("❌ App directory not found")

# Start uvicorn with debug version
try:
    cmd = [sys.executable, "-m", "uvicorn", "app.main_debug:app", "--host", "127.0.0.1", "--port", "8000", "--reload"]
    print(f"Running command: {' '.join(cmd)}")
    subprocess.run(cmd)
except Exception as e:
    print(f"Error: {e}")
finally:
    print("Server stopped")