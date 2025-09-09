# camera_monitor_config.py
# Configuration file for camera disconnection monitoring
import os
import src.logger.custom_logger as custom_logger
import threading
import time
import platform
import subprocess
from datetime import datetime

LOGGER = custom_logger.get_logger()

class CameraMonitorConfig:
    """Configuration settings for camera disconnection monitoring"""
    
    # ENABLE/DISABLE MONITORING
    ENABLED = True  # Set to False to disable camera monitoring completely
    
    # SHUTDOWN TIMING
    SHUTDOWN_DELAY_SECONDS = 15  # Time to wait before shutdown after disconnect (seconds)
    STARTUP_DELAY_SECONDS = 3    # Time to wait before starting monitoring (seconds)
    
    # DETECTION SETTINGS
    CHECK_INTERVAL_SECONDS = 2   # How often to check camera status (seconds)
    MAX_CONSECUTIVE_FAILURES = 3 # Number of consecutive failures to confirm disconnect
    
    # UI NOTIFICATIONS
    SHOW_COUNTDOWN_IN_UI = True  # Show countdown timer in status bar
    SHOW_CAMERA_STATUS = True    # Show camera connection status
    
    # LOGGING
    LOG_CAMERA_CHECKS = False    # Log every camera check (verbose)
    LOG_DISCONNECT_EVENTS = True # Log disconnect/reconnect events
    
    # PLATFORM-SPECIFIC SETTINGS
    WINDOWS_CAMERA_CHECK_TIMEOUT = 5  # Timeout for Windows PowerShell commands
    LINUX_CAMERA_CHECK_TIMEOUT = 5    # Timeout for Linux commands
    
    # ADVANCED SETTINGS
    FORCE_SHUTDOWN_ON_ERROR = True     # Force shutdown even if graceful shutdown fails
    RETRY_CAMERA_DETECTION = True      # Retry camera detection on errors
    
    # CUSTOM MESSAGES
    MESSAGES = {
        'monitoring_started': '📹 Camera monitoring active - will shutdown if disconnected',
        'camera_disconnected': '⚠️ Camera Disconnected! App will close in {}s',
        'camera_reconnected': '✅ Camera Reconnected',
        'shutdown_initiated': '🔌 Camera disconnected - Shutting down...',
        'monitoring_disabled': '⚠️ Camera monitoring disabled'
    }
    
    @classmethod
    def get_message(cls, key, *args):
        """Get formatted message"""
        message = cls.MESSAGES.get(key, 'Unknown status')
        try:
            return message.format(*args)
        except:
            return message


# Updated CameraDisconnectionMonitor with configuration support

class ConfigurableCameraDisconnectionMonitor:
    """Camera monitor with configuration support"""
    
    def __init__(self, app_instance, config=None):
        self.app = app_instance
        self.config = config or CameraMonitorConfig()
        
        # Use config values
        self.shutdown_delay = self.config.SHUTDOWN_DELAY_SECONDS
        self.check_interval = self.config.CHECK_INTERVAL_SECONDS
        self.max_failures = self.config.MAX_CONSECUTIVE_FAILURES
        
        # State variables
        self.is_monitoring = False
        self.camera_connected = True
        self.disconnect_start_time = None
        self.monitor_thread = None
        self.consecutive_failures = 0
        
    def start_monitoring(self):
        """Start monitoring with config check"""
        if not self.config.ENABLED:
            LOGGER.info("Camera monitoring disabled by configuration")
            if self.config.SHOW_CAMERA_STATUS and hasattr(self.app, 'send_feedback_msg'):
                self.app.send_feedback_msg(self.config.get_message('monitoring_disabled'))
            return
            
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        
        if self.config.LOG_DISCONNECT_EVENTS:
            LOGGER.info("Starting camera disconnection monitoring with config...")
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        # Show status in UI
        if self.config.SHOW_CAMERA_STATUS and hasattr(self.app, 'send_feedback_msg'):
            self.app.send_feedback_msg(self.config.get_message('monitoring_started'))
        
    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False
        if self.config.LOG_DISCONNECT_EVENTS:
            LOGGER.info("Camera disconnection monitoring stopped")
        
    def _monitor_loop(self):
        """Main monitoring loop with configuration"""
        self.consecutive_failures = 0
        
        while self.is_monitoring:
            try:
                camera_available = self._is_camera_available()
                
                if self.config.LOG_CAMERA_CHECKS:
                    LOGGER.debug(f"Camera check: {'Available' if camera_available else 'Unavailable'}")
                
                if camera_available:
                    if not self.camera_connected:
                        self._handle_camera_reconnected()
                    self.consecutive_failures = 0
                    
                else:
                    self.consecutive_failures += 1
                    
                    if self.consecutive_failures >= self.max_failures and self.camera_connected:
                        if self.config.LOG_DISCONNECT_EVENTS:
                            LOGGER.warning(f"Camera disconnection confirmed after {self.consecutive_failures} failures")
                        self._handle_camera_disconnected()
                    elif not self.camera_connected:
                        self._check_shutdown_timer()
                        
            except Exception as e:
                LOGGER.error(f"Error in camera monitoring: {e}")
                if self.config.RETRY_CAMERA_DETECTION:
                    self.consecutive_failures += 1
                else:
                    # Treat error as disconnect if retry is disabled
                    if self.camera_connected:
                        self._handle_camera_disconnected()
                
            time.sleep(self.check_interval)
    
    def _is_camera_available(self):
        """Check camera availability with platform detection"""
        system = platform.system()
        
        if system == "Windows":
            return self._check_windows_camera()
        elif system == "Linux":
            return self._check_linux_camera()
        elif system == "Darwin":  # macOS
            return self._check_mac_camera()
        else:
            LOGGER.warning(f"Unsupported platform for camera detection: {system}")
            return True  # Assume available
    
    def _check_windows_camera(self):
        """Windows camera detection with config timeout"""
        try:
            timeout = self.config.WINDOWS_CAMERA_CHECK_TIMEOUT
            
            # Method 1: PowerShell Device Manager check
            cmd = ['powershell', '-Command', 
                   "Get-PnpDevice -Class Camera | Where-Object {$_.Status -eq 'OK'}"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            
            if result.returncode == 0 and result.stdout.strip():
                return True
                
            # Method 2: USB device check for Intel RealSense
            cmd = ['wmic', 'path', 'Win32_USBHub', 'get', 'DeviceID', '/format:list']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            
            # Intel RealSense vendor/device IDs
            realsense_identifiers = ['2AAD', '8086', 'VID_8086', 'VID_2AAD']
            return any(identifier in result.stdout.upper() for identifier in realsense_identifiers)
            
        except subprocess.TimeoutExpired:
            LOGGER.warning("Windows camera check timed out")
            return False
        except Exception as e:
            if self.config.LOG_CAMERA_CHECKS:
                LOGGER.debug(f"Windows camera check failed: {e}")
            return False
    
    def _check_linux_camera(self):
        """Linux camera detection with config timeout"""
        try:
            timeout = self.config.LINUX_CAMERA_CHECK_TIMEOUT
            
            # Method 1: Check video devices
            video_devices = [f'/dev/video{i}' for i in range(10)]
            if any(os.path.exists(device) for device in video_devices):
                return True
                
            # Method 2: Check USB devices via lsusb
            result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=timeout)
            if result.returncode == 0:
                output_upper = result.stdout.upper()
                # Look for Intel or RealSense identifiers
                intel_ids = ['8086:', '2AAD:', 'INTEL', 'REALSENSE']
                if any(identifier in output_upper for identifier in intel_ids):
                    return True
                    
            # Method 3: Check /sys/bus/usb/devices for Intel devices
            usb_path = '/sys/bus/usb/devices'
            if os.path.exists(usb_path):
                for device in os.listdir(usb_path):
                    try:
                        vendor_file = os.path.join(usb_path, device, 'idVendor')
                        if os.path.exists(vendor_file):
                            with open(vendor_file, 'r') as f:
                                vendor_id = f.read().strip().upper()
                                if vendor_id in ['8086', '2AAD']:
                                    return True
                    except:
                        continue
                        
            return False
            
        except subprocess.TimeoutExpired:
            LOGGER.warning("Linux camera check timed out")
            return False
        except Exception as e:
            if self.config.LOG_CAMERA_CHECKS:
                LOGGER.debug(f"Linux camera check failed: {e}")
            return False
    
    def _check_mac_camera(self):
        """macOS camera detection"""
        try:
            timeout = self.config.LINUX_CAMERA_CHECK_TIMEOUT  # Reuse Linux timeout
            
            # Use system_profiler to check USB devices
            cmd = ['system_profiler', 'SPUSBDataType']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            
            if result.returncode == 0:
                output_upper = result.stdout.upper()
                return 'INTEL' in output_upper and 'REALSENSE' in output_upper
                
            return False
            
        except subprocess.TimeoutExpired:
            LOGGER.warning("macOS camera check timed out")
            return False
        except Exception as e:
            if self.config.LOG_CAMERA_CHECKS:
                LOGGER.debug(f"macOS camera check failed: {e}")
            return False
    
    def _handle_camera_disconnected(self):
        """Handle disconnect with countdown UI"""
        self.camera_connected = False
        self.disconnect_start_time = datetime.now()
        
        if self.config.LOG_DISCONNECT_EVENTS:
            LOGGER.warning(f"Camera disconnected! Application will shutdown in {self.shutdown_delay} seconds")
        
        # Update UI
        self._update_disconnect_ui()
        
    def _handle_camera_reconnected(self):
        """Handle reconnection"""
        self.camera_connected = True
        self.disconnect_start_time = None
        
        if self.config.LOG_DISCONNECT_EVENTS:
            LOGGER.info("Camera reconnected - shutdown canceled")
        
        # Update UI
        if self.config.SHOW_CAMERA_STATUS and hasattr(self.app, 'send_feedback_msg'):
            self.app.send_feedback_msg(self.config.get_message('camera_reconnected'))
    
    def _update_disconnect_ui(self):
        """Update UI with disconnect status"""
        try:
            if not self.config.SHOW_CAMERA_STATUS:
                return
                
            if hasattr(self.app, 'send_feedback_msg'):
                message = self.config.get_message('camera_disconnected', self.shutdown_delay)
                self.app.send_feedback_msg(message)
            
            # Update image feedback if available
            if hasattr(self.app, 'image_feedback_frame'):
                self.app.image_feedback_frame.set_error_state("Camera Disconnected - App Shutting Down")
                
        except Exception as e:
            LOGGER.error(f"Failed to update disconnect UI: {e}")
    
    def _check_shutdown_timer(self):
        """Check shutdown timer with countdown UI updates"""
        if not self.disconnect_start_time:
            return
            
        elapsed = datetime.now() - self.disconnect_start_time
        elapsed_seconds = elapsed.total_seconds()
        remaining_seconds = max(0, self.shutdown_delay - elapsed_seconds)
        
        # Update countdown in UI
        if (self.config.SHOW_COUNTDOWN_IN_UI and 
            hasattr(self.app, 'send_feedback_msg') and 
            remaining_seconds > 0):
            
            countdown_msg = self.config.get_message('camera_disconnected', int(remaining_seconds))
            self.app.send_feedback_msg(countdown_msg)
        
        # Check if time to shutdown
        if elapsed_seconds >= self.shutdown_delay:
            if self.config.LOG_DISCONNECT_EVENTS:
                LOGGER.critical("Camera disconnect timeout reached - initiating shutdown")
            self._trigger_shutdown()
    
    def _trigger_shutdown(self):
        """Trigger shutdown with config options"""
        try:
            if self.config.LOG_DISCONNECT_EVENTS:
                LOGGER.info("Triggering application shutdown due to camera disconnection...")
            
            # Final UI update
            if self.config.SHOW_CAMERA_STATUS and hasattr(self.app, 'send_feedback_msg'):
                self.app.send_feedback_msg(self.config.get_message('shutdown_initiated'))
            
            # Schedule shutdown
            if hasattr(self.app, 'after'):
                self.app.after(1000, self._perform_shutdown)
            else:
                self._perform_shutdown()
                
        except Exception as e:
            LOGGER.error(f"Error triggering shutdown: {e}")
            if self.config.FORCE_SHUTDOWN_ON_ERROR:
                os._exit(1)
    
    def _perform_shutdown(self):
        """Perform shutdown with error handling"""
        try:
            if self.config.LOG_DISCONNECT_EVENTS:
                LOGGER.info("Performing application shutdown...")
            
            self.stop_monitoring()
            
            # Try graceful shutdown first
            if hasattr(self.app, 'exit'):
                self.app.exit()
            elif hasattr(self.app, 'quit_app'):
                self.app.quit_app()
            else:
                os._exit(0)
                
        except Exception as e:
            LOGGER.critical(f"Error during shutdown: {e}")
            if self.config.FORCE_SHUTDOWN_ON_ERROR:
                os._exit(1)


# UPDATED INTEGRATION INSTRUCTIONS

"""
COMPLETE INTEGRATION GUIDE:

1. ADD CONFIGURATION FILE:
   Save the CameraMonitorConfig class as 'src/configuration/camera_monitor_config.py'

2. UPDATE IMPORTS in app_authentication.py:
   Add these imports at the top:
   
   import platform
   import subprocess  
   from datetime import datetime, timedelta
   from src.configuration.camera_monitor_config import CameraMonitorConfig, ConfigurableCameraDisconnectionMonitor

3. REPLACE CameraDisconnectionMonitor:
   Use ConfigurableCameraDisconnectionMonitor instead of the basic version

4. UPDATE AuthenticationApplication.__init__:
   Replace the camera monitor initialization with:
   
   # ---Initialize camera disconnect monitor with config---
   self.camera_monitor = ConfigurableCameraDisconnectionMonitor(
       app_instance=self,
       config=CameraMonitorConfig()
   )

5. CUSTOMIZE SETTINGS:
   Edit CameraMonitorConfig values as needed:
   - SHUTDOWN_DELAY_SECONDS: Time before shutdown
   - ENABLED: Enable/disable monitoring  
   - SHOW_COUNTDOWN_IN_UI: Show countdown timer
   - LOG_DISCONNECT_EVENTS: Enable disconnect logging

6. TEST THE SYSTEM:
   - Start application
   - Wait for "Camera monitoring active" message
   - Unplug camera USB cable  
   - Observe countdown and automatic shutdown
   - Reconnect camera to test reconnection logic

7. PRODUCTION DEPLOYMENT:
   - Set ENABLED=True for production
   - Set LOG_CAMERA_CHECKS=False to reduce log noise
   - Adjust SHUTDOWN_DELAY_SECONDS as needed (15-30 seconds recommended)
   - Test on target platform (Windows/Linux specific)
"""