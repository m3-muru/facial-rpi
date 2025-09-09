#!/usr/bin/env python3
"""
Startup Script for ETC Application with Monitoring
Runs both the Flask app and the ETCMon helper together
"""

import subprocess
import sys
import time
import os
import signal
import threading

class ETCStartupManager:
    def __init__(self):
        self.flask_process = None
        self.helper_process = None
        self.running = True
        
    def start_flask_app(self):
        """Start the Flask application"""
        print("Starting Flask monitoring server...")
        try:
            self.flask_process = subprocess.Popen([
                sys.executable, 'flask_app.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            
            # Monitor Flask output in a separate thread
            threading.Thread(target=self._monitor_flask_output, daemon=True).start()
            
        except Exception as e:
            print(f"Error starting Flask app: {e}")
            return False
        return True
    
    def start_helper(self):
        """Start the ETCMon helper"""
        print("Starting ETCMon helper...")
        try:
            self.helper_process = subprocess.Popen([
                sys.executable, 'etcmon_helper.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            
            # Monitor helper output in a separate thread
            threading.Thread(target=self._monitor_helper_output, daemon=True).start()
            
        except Exception as e:
            print(f"Error starting ETCMon helper: {e}")
            return False
        return True
    
    def _monitor_flask_output(self):
        """Monitor Flask app output"""
        while self.running and self.flask_process:
            try:
                line = self.flask_process.stdout.readline()
                if line:
                    print(f"[FLASK] {line.strip()}")
                elif self.flask_process.poll() is not None:
                    break
            except:
                break
    
    def _monitor_helper_output(self):
        """Monitor helper output"""
        while self.running and self.helper_process:
            try:
                line = self.helper_process.stdout.readline()
                if line:
                    print(f"[HELPER] {line.strip()}")
                elif self.helper_process.poll() is not None:
                    break
            except:
                break
    
    def stop_all(self):
        """Stop all processes"""
        print("\nShutting down services...")
        self.running = False
        
        if self.helper_process:
            print("Stopping ETCMon helper...")
            try:
                self.helper_process.terminate()
                self.helper_process.wait(timeout=5)
            except:
                self.helper_process.kill()
        
        if self.flask_process:
            print("Stopping Flask server...")
            try:
                self.flask_process.terminate()
                self.flask_process.wait(timeout=5)
            except:
                self.flask_process.kill()
        
        print("All services stopped.")
    
    def run(self):
        """Main run method"""
        print("=" * 60)
        print("ETC Application Startup Manager")
        print("=" * 60)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Start Flask app first
        if not self.start_flask_app():
            print("Failed to start Flask app. Exiting.")
            return 1
        
        # Wait a moment for Flask to start up
        print("Waiting for Flask server to initialize...")
        time.sleep(3)
        
        # Start helper
        if not self.start_helper():
            print("Failed to start ETCMon helper. Stopping Flask and exiting.")
            self.stop_all()
            return 1
        
        print("\n" + "=" * 60)
        print("All services started successfully!")
        print("Flask server: http://127.0.0.1:5000")
        print("Health endpoint: http://127.0.0.1:5000/health")
        print("Status endpoint: http://127.0.0.1:5000/status")
        print("Press Ctrl+C to stop all services")
        print("=" * 60)
        
        # Keep the main process running
        try:
            while self.running:
                # Check if processes are still running
                if self.flask_process and self.flask_process.poll() is not None:
                    print("Flask process died unexpectedly!")
                    break
                
                if self.helper_process and self.helper_process.poll() is not None:
                    print("Helper process died unexpectedly!")
                    break
                
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_all()
        
        return 0
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\nReceived signal {signum}, shutting down...")
        self.running = False

def main():
    """Main entry point"""
    manager = ETCStartupManager()
    return manager.run()

if __name__ == "__main__":
    sys.exit(main())