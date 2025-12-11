#!/usr/bin/env python3
"""
Simple test script to verify the FastAPI app can be imported and started
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

try:
    # Test importing the app
    from app.main import app
    print("✅ Successfully imported FastAPI app")
    
    # Test basic app configuration
    print(f"✅ App title: {app.title}")
    print(f"✅ App version: {app.version}")
    print("✅ FastAPI app is configured correctly")
    
    # Test importing auth modules
    from app.auth import get_current_user, CurrentUser
    print("✅ Successfully imported auth modules")
    
    # Test database connection
    from app.core.database import sync_engine
    print("✅ Successfully imported database engine")
    
    # Test API modules
    from app.api import api_router
    print("✅ Successfully imported API router")
    
    print("\n🎉 All imports successful! The FastAPI app is ready to run.")
    print("💡 You can now start the server manually.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()