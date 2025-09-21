import subprocess
import sys
import time
import os

def start_backend():
    print("🚀 Starting Weather AI Backend Services...")
    
    services = [
        ("NLP Service", "python backend/NLPService/app.py"),
        ("Ollama Service", "python backend/OllamaService/app.py"),
        ("Playwright Service", "python backend/PlaywrightWeatherService/app.py"),
        ("Main Service", "python backend/MainService/app.py")
    ]
    
    processes = []
    
    for name, command in services:
        print(f"Starting {name}...")
        try:
            process = subprocess.Popen(command, shell=True)
            processes.append((name, process))
            time.sleep(2)
        except Exception as e:
            print(f"Error starting {name}: {e}")
    
    print("\n✅ All services started!")
    print("\n📋 Service URLs:")
    print("Main Service: http://localhost:8000")
    print("NLP Service: http://localhost:8001")
    print("Ollama Service: http://localhost:8002")
    print("Playwright Service: http://localhost:8008")
    print("\nPress Ctrl+C to stop all services")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        for name, process in processes:
            try:
                process.terminate()
                print(f"Stopped {name}")
            except:
                pass

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--mode" and sys.argv[2] == "backend":
        start_backend()
    else:
        print("Usage: python start.py --mode backend")
