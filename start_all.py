#!/usr/bin/env python3
"""
Script pour lancer le frontend et le backend en même temps
"""
import subprocess
import sys
import time
import os
from pathlib import Path

def start_backend():
    """Démarre le backend"""
    print("Starting Backend Services...")
    backend_process = subprocess.Popen([
        sys.executable, "start.py", "--mode", "backend"
    ], cwd=Path.cwd())
    return backend_process

def start_frontend():
    """Démarre le frontend"""
    print("Starting Frontend...")
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("Frontend directory not found!")
        return None
    
    frontend_process = subprocess.Popen([
        "npm", "start"
    ], cwd=frontend_dir)
    return frontend_process

def main():
    print("Starting Weather AI - Full Stack")
    print("=" * 50)
    
    backend = start_backend()
    time.sleep(5)
    
    frontend = start_frontend()
    
    if frontend is None:
        print("Failed to start frontend")
        backend.terminate()
        return
    
    print("\nBoth services started!")
    print("URLs:")
    print("   Frontend: http://localhost:3000")
    print("   Backend:  http://localhost:8000")
    print("\nPress Ctrl+C to stop all services")
    
    try:
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        print("\nStopping all services...")
        backend.terminate()
        frontend.terminate()
        print("All services stopped!")

if __name__ == "__main__":
    main()
