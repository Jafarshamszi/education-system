#!/usr/bin/env python3
"""
Setup script for Education Management System Backend
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return None


def main():
    """Main setup function"""
    print("🏗️  Setting up Education Management System Backend")
    
    # Check if we're in the backend directory
    if not os.path.exists("requirements.txt"):
        print("❌ Please run this script from the backend directory")
        sys.exit(1)
    
    # Create virtual environment
    if not os.path.exists("venv"):
        run_command("python -m venv venv", "Creating virtual environment")
    
    # Activate virtual environment and install dependencies
    if sys.platform == "win32":
        pip_command = "venv\\Scripts\\pip"
        python_command = "venv\\Scripts\\python"
    else:
        pip_command = "venv/bin/pip"
        python_command = "venv/bin/python"
    
    # Upgrade pip
    run_command(f"{pip_command} install --upgrade pip", "Upgrading pip")
    
    # Install dependencies
    run_command(f"{pip_command} install -r requirements.txt", 
                "Installing Python dependencies")
    
    # Copy environment file
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            run_command("cp .env.example .env", "Creating .env file")
            print("📝 Please edit .env file with your database credentials")
        else:
            print("⚠️  .env.example not found, please create .env manually")
    
    # Initialize Alembic
    if not os.path.exists("alembic"):
        run_command(f"{python_command} -m alembic init alembic", 
                    "Initializing Alembic migrations")
    
    print("\n🎉 Setup completed!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your PostgreSQL credentials")
    print("2. Ensure PostgreSQL is running")
    print("3. Create the database: createdb education_system")
    print("4. Run: python -m alembic revision --autogenerate -m 'Initial migration'")
    print("5. Run: python -m alembic upgrade head")
    print("6. Start the server: uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()