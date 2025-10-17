#!/usr/bin/env python3
"""
Newsletter Application Startup Script
"""
import sys
import asyncio
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.main import scheduler, run_scheduler, health_check, graceful_shutdown
from router.routes import bp
from launch import app
import signal
import threading

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\nReceiving shutdown signal...")
    graceful_shutdown()
    sys.exit(0)

def start_web_server():
    """Start Flask web server"""
    print("Starting web server on http://localhost:5001")
    app.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False)

def start_scheduler(task_type="daily"):
    """Start newsletter scheduler"""
    print(f"Starting {task_type} scheduler...")
    run_scheduler(task_type)

def main():
    """Main application entry point"""
    print("Starting Newsletter Application...")
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check system health
    health = health_check()
    print(f"System Health: {health['status']}")
    
    if health['status'] != 'healthy':
        print("[WARNING] System health check failed:")
        for check, status in health['checks'].items():
            print(f"  {check}: {'[OK]' if status else '[FAIL]'}")
        
        # Check if critical systems are working
        critical_checks = ['scheduler_initialized', 'config_files_exist']
        critical_failed = [check for check in critical_checks if not health['checks'].get(check, False)]
        
        if critical_failed:
            print(f"\nCritical systems failed: {critical_failed}")
            print("Please fix these issues before starting the application.")
            return
        else:
            print("\nNon-critical issues detected, but application can start.")
    
    if health['status'] == 'healthy':
        print("[OK] All systems healthy!")
    else:
        print("[OK] Critical systems healthy!")
    print(f"Loaded {len(scheduler.subscribers)} subscribers")
    
    # Start web server in background thread
    web_thread = threading.Thread(target=start_web_server, daemon=True)
    web_thread.start()
    
    print("\nAvailable commands:")
    print("  1. Start daily scheduler")
    print("  2. Start weekly scheduler") 
    print("  3. Run web server only")
    print("  4. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == "1":
                start_scheduler("daily")
                break
            elif choice == "2":
                start_scheduler("weekly")
                break
            elif choice == "3":
                print("Web server running at http://localhost:5001")
                print("Press Ctrl+C to stop")
                try:
                    while True:
                        pass
                except KeyboardInterrupt:
                    break
            elif choice == "4":
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please enter 1-4.")
                
        except KeyboardInterrupt:
            break
    
    graceful_shutdown()

if __name__ == "__main__":
    main()