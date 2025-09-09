import requests
import socket
import threading
import time
from datetime import datetime
import src.logger.custom_logger as custom_logger

LOGGER = custom_logger.get_logger()

class ETCConnectionMonitor:
    """
    Monitors connection to ETC.xhtml and provides status updates
    """
    
    def __init__(self, etc_base_url="http://localhost:8080"):
        self.etc_base_url = etc_base_url
        self.etc_full_url = f"{etc_base_url}/psms/mcs/ETC.xhtml?mode=facial&inout=O"
        
        # Connection status
        self.is_etc_reachable = False
        self.is_websocket_connected = False
        self.last_check_time = None
        self.connection_failures = 0
        self.max_failures = 3
        
        # Monitoring settings
        self.check_interval = 30
        self.timeout = 10
        self.is_monitoring = False
        
        # Callbacks for status changes
        self.status_callbacks = []
        
    def add_status_callback(self, callback):
        """Add a callback function to be called when connection status changes"""
        self.status_callbacks.append(callback)
        
    def _notify_status_change(self, status_type, is_connected, details=None):
        """Notify all callbacks of status changes"""
        for callback in self.status_callbacks:
            try:
                callback(status_type, is_connected, details)
            except Exception as e:
                LOGGER.error(f"Error in status callback: {e}")
    
    def check_etc_web_page(self):
        """Check if ETC.xhtml is reachable via HTTP"""
        try:
            response = requests.get(self.etc_full_url, timeout=self.timeout, allow_redirects=True)
            
            if response.status_code == 200 and ("ETC" in response.text or "Employee ID" in response.text):
                if not self.is_etc_reachable:
                    LOGGER.info("ETC web page connection established")
                    self._notify_status_change("etc_web", True, {"url": self.etc_full_url})
                
                self.is_etc_reachable = True
                self.connection_failures = 0
                return True
            else:
                return False
                
        except Exception as e:
            LOGGER.debug(f"ETC page check failed: {e}")
            if self.is_etc_reachable:
                self.connection_failures += 1
                if self.connection_failures >= self.max_failures:
                    self._notify_status_change("etc_web", False, {"url": self.etc_full_url})
                    self.is_etc_reachable = False
            return False
    
    def check_websocket_endpoint(self):
        """Check if WebSocket endpoint is available"""
        try:
            url_parts = self.etc_base_url.replace('http://', '').replace('https://', '')
            hostname = url_parts.split(':')[0]
            port = int(url_parts.split(':')[1]) if ':' in url_parts else 80
            
            sock = socket.create_connection((hostname, port), timeout=self.timeout)
            sock.close()
            
            if not self.is_websocket_connected:
                self._notify_status_change("websocket", True, {"endpoint": f"{hostname}:{port}"})
            
            self.is_websocket_connected = True
            return True
            
        except Exception as e:
            if self.is_websocket_connected:
                self._notify_status_change("websocket", False, {"error": str(e)})
            self.is_websocket_connected = False
            return False
    
    def get_connection_status(self):
        """Get current connection status"""
        return {
            "etc_web_reachable": self.is_etc_reachable,
            "websocket_reachable": self.is_websocket_connected,
            "last_check": self.last_check_time.isoformat() if self.last_check_time else None,
            "overall_status": self.get_overall_status()
        }
    
    def get_overall_status(self):
        """Get overall connection status"""
        if self.is_etc_reachable and self.is_websocket_connected:
            return "fully_connected"
        elif self.is_etc_reachable or self.is_websocket_connected:
            return "partially_connected"
        else:
            return "disconnected"
    
    def perform_full_check(self):
        """Perform a full connectivity check"""
        self.last_check_time = datetime.now()
        self.check_etc_web_page()
        self.check_websocket_endpoint()
        return self.get_connection_status()
    
    def start_monitoring(self):
        """Start continuous monitoring"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        LOGGER.info(f"Starting ETC connection monitoring")
        
        def monitoring_loop():
            while self.is_monitoring:
                try:
                    self.perform_full_check()
                    time.sleep(self.check_interval)
                except Exception as e:
                    LOGGER.error(f"Error in ETC monitoring: {e}")
                    time.sleep(self.check_interval)
        
        self.monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.monitoring_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False
    
    def test_connection_now(self):
        """Test connection immediately"""
        return self.perform_full_check()
