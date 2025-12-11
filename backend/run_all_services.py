#!/usr/bin/env python3
"""
Startup script to run both FastAPI and Django services
"""

import os
import sys
import subprocess
import time
from pathlib import Path


def run_fastapi():
    """Run FastAPI service on port 8000"""
    print("🚀 Starting FastAPI service on port 8000...")
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    return subprocess.Popen([
        sys.executable, "start_server.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def run_django():
    """Run Django service on port 8001"""
    print("🚀 Starting Django service on port 8001...")
    django_dir = Path(__file__).parent / "django_backend" / "education_system"
    os.chdir(django_dir)
    
    return subprocess.Popen([
        sys.executable, "manage.py", "runserver", "8001"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def main():
    """Main function to start both services"""
    print("🎯 Education System Backend Services Launcher")
    print("=" * 50)
    
    processes = []
    
    try:
        # Start FastAPI service
        fastapi_process = run_fastapi()
        processes.append(fastapi_process)
        time.sleep(2)  # Give it time to start
        
        # Start Django service 
        django_process = run_django()
        processes.append(django_process)
        time.sleep(2)  # Give it time to start
        
        print("\n✅ Services Started Successfully!")
        print("📡 FastAPI Service: http://localhost:8000")
        print("📊 FastAPI Docs: http://localhost:8000/docs")
        print("🎓 Django Service: http://localhost:8001")
        print("👥 Teachers API: http://localhost:8001/api/v1/teachers/")
        print("\n⚠️  Press Ctrl+C to stop all services")
        
        # Wait for processes to complete or interruption
        while True:
            time.sleep(1)
            
            # Check if any process has died
            for i, process in enumerate(processes):
                if process.poll() is not None:
                    service_name = "FastAPI" if i == 0 else "Django"
                    print(f"\n❌ {service_name} service stopped unexpectedly!")
                    
                    # Get error output
                    stdout, stderr = process.communicate()
                    if stderr:
                        print(f"Error: {stderr.decode()}")
                    return
                    
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down services...")
        
        # Terminate all processes
        for i, process in enumerate(processes):
            service_name = "FastAPI" if i == 0 else "Django"
            print(f"   Stopping {service_name} service...")
            
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"   Force killing {service_name} service...")
                process.kill()
                process.wait()
        
        print("✅ All services stopped successfully!")
        
    except Exception as e:
        print(f"\n❌ Error starting services: {e}")
        
        # Clean up any running processes
        for process in processes:
            try:
                process.terminate()
                process.wait(timeout=3)
            except Exception:
                process.kill()


if __name__ == "__main__":
    main()
