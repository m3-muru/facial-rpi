#!/usr/bin/env python3
"""
ETCMon Helper Script
Monitors the Flask app health and posts heartbeat data to the ETCMON server
"""

import requests
import time
import json
import socket
import datetime
import sys
import os

# Configuration
FLASK_APP_URL = 'http://127.0.0.1:5000'
HEALTH_ENDPOINT = '/health'
STATUS_ENDPOINT = '/status'
CHECK_INTERVAL_SECONDS = 5
ETCMON_UPDATE_INTERVAL_SECONDS = 30  # Post to ETCMON every 30 seconds

# ETCMON server configuration - update these values as needed
ETCMON_APP_URL = 'http://your-etcmon-server:port'  # Update with actual ETCMON server URL
CLIENT_NAME = 'lift_lobby_etc01'  # Update with actual client name

class ETCMonHelper:
    def __init__(self):
        self.hostname = socket.gethostname()
        self.ip_address = socket.gethostbyname(self.hostname)
        self.last_etcmon_post = 0
        self.flask_app_healthy = False
        self.last_health_data = None
        
    def post_to_etcmon(self, health_data=None):
        """
        Posts heartbeat data to the ETCMON server.
        """
        UPDATE_URL = f"{ETCMON_APP_URL}/update"
        
        # Prepare data payload
        data = {
            "hostname": self.hostname,
            "ip_address": self.ip_address,
            "client_name": CLIENT_NAME,
            "timestamp": datetime.datetime.now().isoformat(),
            "status": "online" if self.flask_app_healthy else "offline"
        }
        
        # Add health data if available
        if health_data:
            data.update({
                "health_status": health_data.get('health', 'unknown'),
                "station_id": health_data.get('details', {}).get('station_id'),
                "uptime_seconds": health_data.get('details', {}).get('uptime_seconds', 0),
                "main_app_running": health_data.get('details', {}).get('main_app_running', False)
            })
        
        # Set the headers to indicate that the content is JSON
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "ETCMon-Helper/1.0"
        }

        try:
            response = requests.post(UPDATE_URL, data=json.dumps(data), headers=headers, timeout=10)
           
            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                print(f"[{self._timestamp()}] Heartbeat successfully posted to ETCMON.")
                if response.text:
                    print(f"Server response: {response.text}")
            else:
                print(f"[{self._timestamp()}] Failed to post heartbeat. Status code: {response.status_code}")
                print(f"Server response: {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"[{self._timestamp()}] Error connecting to ETCMON server: {e}")

    def check_flask_app(self):
        """
        Sends a request to the Flask app's health endpoint and reports the status.
        Returns the health data if successful, None otherwise.
        """
        try:
            response = requests.get(f"{FLASK_APP_URL}{HEALTH_ENDPOINT}", timeout=5)

            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'ok':
                    health = data.get('health', 'unknown')
                    details = data.get('details', {})
                    
                    # Determine if app is healthy
                    self.flask_app_healthy = health in ['healthy', 'starting']
                    
                    print(f"[{self._timestamp()}] Flask app health: {health}")
                    print(f"  Station ID: {details.get('station_id', 'N/A')}")
                    print(f"  Main App Running: {details.get('main_app_running', 'N/A')}")
                    print(f"  Uptime: {details.get('uptime_human', 'N/A')}")
                    
                    self.last_health_data = data
                    return data
                else:
                    print(f"[{self._timestamp()}] Flask app unhealthy. Unexpected response: {data}")
                    self.flask_app_healthy = False
            else:
                print(f"[{self._timestamp()}] Flask app unhealthy. Status code: {response.status_code}")
                self.flask_app_healthy = False

        except requests.exceptions.RequestException as e:
            print(f"[{self._timestamp()}] Connection error: Could not reach Flask app. Error: {e}")
            self.flask_app_healthy = False
            
        return None

    def get_detailed_status(self):
        """
        Get detailed status information from the Flask app
        """
        try:
            response = requests.get(f"{FLASK_APP_URL}{STATUS_ENDPOINT}", timeout=5)
            if response.status_code == 200:
                return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[{self._timestamp()}] Error getting detailed status: {e}")
        return None

    def _timestamp(self):
        """Get current timestamp string"""
        return time.strftime('%Y-%m-%d %H:%M:%S')

    def run_monitoring_loop(self):
        """
        Main monitoring loop
        """
        print(f"[{self._timestamp()}] Starting ETCMon Helper...")
        print(f"Flask app URL: {FLASK_APP_URL}")
        print(f"ETCMON server URL: {ETCMON_APP_URL}")
        print(f"Client name: {CLIENT_NAME}")
        print(f"Health check interval: {CHECK_INTERVAL_SECONDS} seconds")
        print(f"ETCMON update interval: {ETCMON_UPDATE_INTERVAL_SECONDS} seconds")
        print("-" * 60)
        
        while True:
            # Check Flask app health
            health_data = self.check_flask_app()
            
            # Post to ETCMON periodically
            current_time = time.time()
            if current_time - self.last_etcmon_post >= ETCMON_UPDATE_INTERVAL_SECONDS:
                self.post_to_etcmon(health_data)
                self.last_etcmon_post = current_time
            
            # Wait before next check
            time.sleep(CHECK_INTERVAL_SECONDS)

def main():
    """
    Main entry point
    """
    try:
        helper = ETCMonHelper()
        helper.run_monitoring_loop()
    except KeyboardInterrupt:
        print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] ETCMon Helper stopped by user")
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()