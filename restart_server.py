#!/usr/bin/env python3
"""
Script to restart the server and bot
"""
import subprocess
import sys
import os
import signal
import time

def stop_existing_processes():
    """Stop any existing server processes"""
    try:
        # Find and kill any existing uvicorn processes running our app
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'uvicorn' in proc.info['cmdline'] and 'main:app' in proc.info['cmdline']:
                    print(f"Stopping existing process PID {proc.info['pid']}")
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except ImportError:
        # If psutil is not available, use system command
        os.system("pkill -f 'uvicorn.*main:app' 2>/dev/null")

def start_server_and_bot():
    """Start the server with integrated bot"""
    print("Starting server with integrated bot...")
    
    # Change to the project directory
    project_dir = "/home/avhan3/Dokumen/PROGRAM/Next JS/skripsi"
    os.chdir(project_dir)
    
    # Activate virtual environment and start the server
    cmd = [
        "uvicorn", 
        "main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000",
        "--reload"  # Enable auto-reload for development
    ]
    
    try:
        # Start the server process
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(f"Server started with PID: {process.pid}")
        print("Server is starting... Please wait.")
        
        # Wait a bit to see if there are any immediate errors
        time.sleep(2)
        
        # Check if the process is still running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print("STDOUT:", stdout)
            print("STDERR:", stderr)
            print("Server failed to start properly")
            return False
        else:
            print("✓ Server started successfully!")
            print("✓ Bot should start automatically (integrated in main.py)")
            print("✓ Access the application at: http://localhost:8000")
            return True
            
    except Exception as e:
        print(f"Error starting server: {e}")
        return False

def main():
    print("🔄 Restarting Server and Bot...")
    
    # Stop existing processes
    print("Stopping existing processes...")
    stop_existing_processes()
    time.sleep(2)  # Wait for processes to stop
    
    # Start the server and bot
    success = start_server_and_bot()
    
    if success:
        print("")
        print("🎉 Restart completed successfully!")
        print("💡 The server is running with the bot integrated.")
        print("💡 Bot should be operational and listening for commands.")
    else:
        print("")
        print("❌ Restart failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
