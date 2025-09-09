#!/usr/bin/env python3
"""
Quick Integration Script for ETC Connection Monitoring

This script adds ETC connection monitoring to your existing authentication application.
Run this script to automatically integrate the monitoring features.
"""

import os
import sys
import shutil
from pathlib import Path

def create_etc_connection_monitor():
    """Create the ETC connection monitor file"""
    
    monitor_code = '''import requests
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
'''
    
    # Create directory if it doesn't exist
    monitor_dir = Path("src/network_comms")
    monitor_dir.mkdir(parents=True, exist_ok=True)
    
    # Write the monitor file
    monitor_file = monitor_dir / "etc_connection_monitor.py"
    with open(monitor_file, 'w', encoding='utf-8') as f:
        f.write(monitor_code)
    
    print(f" Created ETC connection monitor: {monitor_file}")
    return monitor_file

def patch_authentication_app():
    """Patch the main authentication app"""
    
    app_file = Path("app_authentication.py")
    if not app_file.exists():
        print(" app_authentication.py not found")
        return False
    
    # Read current content
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add import if not present
    import_line = "from src.network_comms.etc_connection_monitor import ETCConnectionMonitor"
    if import_line not in content:
        # Find existing imports
        import_section = content.find("import src.logger.custom_logger as custom_logger")
        if import_section != -1:
            # Add after the custom_logger import
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "import src.logger.custom_logger as custom_logger" in line:
                    lines.insert(i + 1, "from src.network_comms.etc_connection_monitor import ETCConnectionMonitor")
                    break
            content = '\n'.join(lines)
    
    # Add ETC monitoring initialization
    init_method_start = content.find("def __init__(self, parent):")
    if init_method_start != -1:
        # Find the end of __init__ method
        heartbeat_line = content.find("self.start_app_status_heartbeat()")
        if heartbeat_line != -1:
            # Add ETC monitoring after heartbeat
            etc_init_code = '''
        # ---ETC Connection Monitoring---
        try:
            self.etc_monitor = ETCConnectionMonitor("http://localhost:8080")
            self.etc_monitor.add_status_callback(self.on_etc_status_change)
            self.etc_monitor.start_monitoring()
            self.etc_monitor.test_connection_now()
            LOGGER.info("ETC connection monitoring initialized")
        except Exception as e:
            LOGGER.error(f"Failed to initialize ETC monitoring: {e}")
            self.etc_monitor = None'''
            
            # Find the end of the heartbeat line
            heartbeat_end = content.find('\n', heartbeat_line)
            content = content[:heartbeat_end] + etc_init_code + content[heartbeat_end:]
    
    # Add status callback method
    if "def on_etc_status_change" not in content:
        callback_method = '''
    def on_etc_status_change(self, status_type, is_connected, details=None):
        """Handle ETC connection status changes"""
        try:
            if hasattr(self, 'status_bar') and self.status_bar:
                if status_type == "etc_web":
                    msg = " ETC Web Connected" if is_connected else " ETC Web Disconnected"
                    status = 'success' if is_connected else 'danger'
                elif status_type == "websocket":
                    msg = " ETC WebSocket Connected" if is_connected else "⚠️ ETC WebSocket Issue"
                    status = 'success' if is_connected else 'warning'
                else:
                    return
                
                # Update status bar
                self.status_bar.set_feedback({"msg": msg, "status": status})
                
        except Exception as e:
            LOGGER.error(f"Error in ETC status callback: {e}")
'''
        
        # Add the method before the last method in the class
        last_method_pos = content.rfind("def ")
        if last_method_pos != -1:
            # Find the start of the line
            line_start = content.rfind('\n', 0, last_method_pos)
            content = content[:line_start] + callback_method + content[line_start:]
    
    # Add cleanup in exit method
    exit_method_pos = content.find("def exit(self):")
    if exit_method_pos != -1:
        # Find the line with os._exit(0)
        os_exit_pos = content.find("os._exit(0)", exit_method_pos)
        if os_exit_pos != -1:
            cleanup_code = '''
        # Stop ETC monitoring
        if hasattr(self, 'etc_monitor') and self.etc_monitor:
            try:
                self.etc_monitor.stop_monitoring()
                LOGGER.info("ETC monitoring stopped")
            except Exception as e:
                LOGGER.error(f"Error stopping ETC monitoring: {e}")
        '''
            # Add before os._exit(0)
            line_start = content.rfind('\n', 0, os_exit_pos)
            content = content[:line_start] + cleanup_code + content[line_start:]
    
    # Write the patched content
    backup_file = app_file.with_suffix('.py.backup')
    shutil.copy2(app_file, backup_file)
    
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f" Patched {app_file} (backup saved as {backup_file})")
    return True

def patch_modern_app():
    """Patch the modern authentication app"""
    
    app_file = Path("modern_app_authentication.py")
    if not app_file.exists():
        print("⚠️ modern_app_authentication.py not found, skipping")
        return False
    
    # Read current content
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add import
    import_line = "from src.network_comms.etc_connection_monitor import ETCConnectionMonitor"
    if import_line not in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "import src.logger.custom_logger as custom_logger" in line:
                lines.insert(i + 1, import_line)
                break
        content = '\n'.join(lines)
    
    # Add ETC section in create_single_column_content
    system_section_pos = content.find("# 5. System information section")
    if system_section_pos != -1:
        etc_section_code = '''
        # 6. ETC Connection Status section
        try:
            etc_section = self.create_section_container(
                content_container,
                " ETC Status"
            )
            
            # Create ETC monitor
            self.etc_monitor = ETCConnectionMonitor("http://localhost:8080")
            
            # Create simple status display
            self.create_etc_status_display(etc_section)
            
            # Start monitoring
            self.etc_monitor.add_status_callback(self.on_etc_status_change)
            self.etc_monitor.start_monitoring()
            self.etc_monitor.test_connection_now()
            
        except Exception as e:
            LOGGER.error(f"Failed to add ETC monitoring: {e}")
            self.etc_monitor = None
'''
        
        # Find the end of system section
        next_section_pos = content.find("# 6.", system_section_pos + 1)
        if next_section_pos == -1:
            next_section_pos = content.find("# Footer section", system_section_pos)
        
        if next_section_pos != -1:
            content = content[:next_section_pos] + etc_section_code + '\n        ' + content[next_section_pos:]
    
    # Add ETC status display method
    if "def create_etc_status_display" not in content:
        etc_display_method = '''
    def create_etc_status_display(self, parent):
        """Create simple ETC status display for 400px width"""
        # Simple status container
        status_container = tk.Frame(parent, bg=MODERN_COLORS['surface_light'], height=40)
        status_container.pack(fill=X, padx=5, pady=5)
        status_container.pack_propagate(False)
        
        # Status indicator
        self.etc_status_dot = tk.Label(
            status_container,
            text="●",
            font=('Segoe UI', 12),
            bg=MODERN_COLORS['surface_light'],
            fg=MODERN_COLORS['danger']
        )
        self.etc_status_dot.pack(side=LEFT, padx=(10, 5), pady=10)
        
        # Status text
        self.etc_status_text = tk.Label(
            status_container,
            text="ETC: Checking...",
            font=('Segoe UI', 10, 'bold'),
            bg=MODERN_COLORS['surface_light'],
            fg=MODERN_COLORS['text_primary']
        )
        self.etc_status_text.pack(side=LEFT, pady=10)
        
        # Test button
        self.etc_test_btn = tk.Button(
            status_container,
            text="🔄",
            font=('Segoe UI', 8),
            bg=MODERN_COLORS['info'],
            fg='white',
            relief='flat',
            bd=0,
            width=3,
            command=self.test_etc_connection
        )
        self.etc_test_btn.pack(side=RIGHT, padx=10, pady=8)
    
    def test_etc_connection(self):
        """Test ETC connection manually"""
        if hasattr(self, 'etc_monitor') and self.etc_monitor:
            self.etc_test_btn.configure(text="⏳")
            threading.Thread(target=self._run_etc_test, daemon=True).start()
    
    def _run_etc_test(self):
        """Run ETC test in background"""
        try:
            if self.etc_monitor:
                self.etc_monitor.test_connection_now()
        finally:
            self.after_idle(lambda: self.etc_test_btn.configure(text="🔄"))
    
    def on_etc_status_change(self, status_type, is_connected, details=None):
        """Handle ETC status changes"""
        self.after_idle(lambda: self._update_etc_status())
    
    def _update_etc_status(self):
        """Update ETC status display"""
        if not hasattr(self, 'etc_monitor') or not self.etc_monitor:
            return
            
        try:
            status = self.etc_monitor.get_connection_status()
            overall = status.get('overall_status', 'disconnected')
            
            if overall == "fully_connected":
                self.etc_status_dot.configure(fg=MODERN_COLORS['success'])
                self.etc_status_text.configure(text="ETC: Connected ✓", fg=MODERN_COLORS['success'])
            elif overall == "partially_connected":
                self.etc_status_dot.configure(fg=MODERN_COLORS['warning'])
                self.etc_status_text.configure(text="ETC: Partial ⚠", fg=MODERN_COLORS['warning'])
            else:
                self.etc_status_dot.configure(fg=MODERN_COLORS['danger'])
                self.etc_status_text.configure(text="ETC: Disconnected ✗", fg=MODERN_COLORS['danger'])
                
        except Exception as e:
            LOGGER.error(f"Error updating ETC status: {e}")
'''
        
        # Add before the last method
        last_method_pos = content.rfind("def ")
        if last_method_pos != -1:
            line_start = content.rfind('\n', 0, last_method_pos)
            content = content[:line_start] + etc_display_method + content[line_start:]
    
    # Add cleanup in exit method
    exit_method_pos = content.find("def exit(self):")
    if exit_method_pos != -1:
        os_exit_pos = content.find("os._exit(0)", exit_method_pos)
        if os_exit_pos != -1:
            cleanup_code = '''
        # Stop ETC monitoring
        if hasattr(self, 'etc_monitor') and self.etc_monitor:
            self.etc_monitor.stop_monitoring()
        '''
            line_start = content.rfind('\n', 0, os_exit_pos)
            content = content[:line_start] + cleanup_code + content[line_start:]
    
    # Write the patched content
    backup_file = app_file.with_suffix('.py.backup')
    shutil.copy2(app_file, backup_file)
    
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f" Patched {app_file} (backup saved as {backup_file})")
    return True

def create_test_script():
    """Create a test script for ETC monitoring"""
    
    test_code = '''#!/usr/bin/env python3
"""
ETC Connection Monitoring Test Script

Run this script to test the ETC connection monitoring functionality.
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

try:
    from src.network_comms.etc_connection_monitor import ETCConnectionMonitor
    print(" ETCConnectionMonitor imported successfully")
except ImportError as e:
    print(f" Failed to import ETCConnectionMonitor: {e}")
    sys.exit(1)

def test_etc_monitoring():
    """Test ETC connection monitoring"""
    print("🔄 Starting ETC Connection Test...")
    print("-" * 50)
    
    # Create monitor
    monitor = ETCConnectionMonitor("http://localhost:8080")
    
    # Add callback to see status updates
    def status_callback(status_type, is_connected, details=None):
        status = " Connected" if is_connected else " Disconnected"
        print(f" {status_type.upper()}: {status}")
        if details:
            print(f"   Details: {details}")
    
    monitor.add_status_callback(status_callback)
    
    # Test immediate connection
    print(" Testing immediate connection...")
    status = monitor.test_connection_now()
    
    print("\\n Connection Status Summary:")
    print(f"   ETC Web: {'' if status['etc_web_reachable'] else ''}")
    print(f"   WebSocket: {'' if status['websocket_reachable'] else ''}")
    print(f"   Overall: {status['overall_status']}")
    
    if status['last_check']:
        print(f"   Last Check: {status['last_check']}")
    
    # Start continuous monitoring
    print("\\n🔄 Starting continuous monitoring for 30 seconds...")
    monitor.start_monitoring()
    
    try:
        time.sleep(30)
    except KeyboardInterrupt:
        print("\\n Test interrupted by user")
    finally:
        monitor.stop_monitoring()
        print("\\n Test completed")

if __name__ == "__main__":
    test_etc_monitoring()
'''
    
    test_file = Path("test_etc_monitoring.py")
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_code)
    
    # Make executable on Unix systems
    if sys.platform != 'win32':
        os.chmod(test_file, 0o755)
    
    print(f" Created test script: {test_file}")
    return test_file

def update_status_bar():
    """Update status bar to handle ETC status better"""
    
    status_bar_file = Path("src/GUI_authentication/status_bar.py")
    if not status_bar_file.exists():
        print("⚠️ status_bar.py not found, skipping enhancement")
        return False
    
    # Read current content
    with open(status_bar_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add ETC-specific status handling
    if "# ETC status enhancement" not in content:
        enhancement_code = '''
    # ETC status enhancement
    def set_etc_status(self, status_type, is_connected, message=None):
        """Set ETC-specific status"""
        if message is None:
            if status_type == "etc_web":
                message = "ETC Web Connected" if is_connected else "ETC Web Disconnected"
            elif status_type == "websocket":
                message = "ETC WebSocket Connected" if is_connected else "ETC WebSocket Issue"
            else:
                message = f"ETC {status_type} {'Connected' if is_connected else 'Disconnected'}"
        
        # Determine status for coloring
        if is_connected:
            status = "success" if "web" in status_type.lower() else "info"
        else:
            status = "danger" if "web" in status_type.lower() else "warning"
        
        # Set the message
        self.set_feedback({"msg": message, "status": status})
'''
        
        # Add before the last method
        last_method_pos = content.rfind("def ")
        if last_method_pos != -1:
            line_start = content.rfind('\n', 0, last_method_pos)
            content = content[:line_start] + enhancement_code + content[line_start:]
            
            # Write enhanced file
            backup_file = status_bar_file.with_suffix('.py.backup')
            shutil.copy2(status_bar_file, backup_file)
            
            with open(status_bar_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f" Enhanced {status_bar_file}")
            return True
    
    return False

def main():
    """Main integration function"""
    print("🚀 ETC Connection Monitoring Integration")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("app_authentication.py").exists():
        print(" Please run this script from the project root directory (where app_authentication.py is located)")
        sys.exit(1)
    
    try:
        # Step 1: Create ETC connection monitor
        print("\\n📁 Creating ETC connection monitor...")
        create_etc_connection_monitor()
        
        # Step 2: Patch main authentication app
        print("\\n🔧 Patching main authentication app...")
        patch_authentication_app()
        
        # Step 3: Patch modern authentication app
        print("\\n🔧 Patching modern authentication app...")
        patch_modern_app()
        
        # Step 4: Update status bar
        print("\\n🔧 Enhancing status bar...")
        update_status_bar()
        
        # Step 5: Create test script
        print("\\n📝 Creating test script...")
        create_test_script()
        
        print("\\n" + "=" * 50)
        print(" ETC Connection Monitoring Integration Complete!")
        print("\\n📋 What was added:")
        print("   • ETC connection monitor (checks web page & websocket)")
        print("   • Status updates in the application status bar")
        print("   • Automatic monitoring every 30 seconds")
        print("   • Manual test functionality")
        print("   • Proper cleanup on application exit")
        
        print("\\n🧪 To test the integration:")
        print("   1. Run: python test_etc_monitoring.py")
        print("   2. Start your application normally")
        print("   3. Check the status bar for ETC connection status")
        
        print("\\n⚠️ Note:")
        print("   • Backup files (.backup) were created for safety")
        print("   • Make sure ETC server is running at http://localhost:8080")
        print("   • The monitoring will show connection status in real-time")
        
        print("\\n🔄 To undo changes:")
        print("   • Restore from .backup files if needed")
        
    except Exception as e:
        print(f"\\n Integration failed: {e}")
        print("\\nPlease check the error and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()