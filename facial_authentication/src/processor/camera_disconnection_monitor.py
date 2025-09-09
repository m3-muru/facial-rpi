# Camera Disconnection Detection and Auto-Shutdown System

import threading
import time
import os
import sys
import platform
import subprocess
from datetime import datetime, timedelta
import src.logger.custom_logger as custom_logger

LOGGER = custom_logger.get_logger()

class CameraDisconnectionMonitor:
    """
    Monitors camera connection status and triggers application shutdown
    when camera is disconnected for a specified duration
    """
    
    def __init__(self, app_instance, shutdown_delay=10):
        """
        Initialize camera monitor
        
        Args:
            app_instance: Reference to main application instance
            shutdown_delay: Seconds to wait before shutdown after camera disconnect (default: 10)
        """
        self.app = app_instance
        self.shutdown_delay = shutdown_delay
        self.is_monitoring = False
        self.camera_connected = True
        self.disconnect_start_time = None
        self.monitor_thread = None
        self.check_interval = 2  # Check every 2 seconds
        
        # Camera detection methods by platform
        self.detection_methods = {
            'Windows': self._check_windows_camera,
            'Linux': self._check_linux_camera,
            'Darwin': self._check_mac_camera  # macOS
        }
        
    def start_monitoring(self):
        """Start camera disconnection monitoring"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        LOGGER.info("Starting camera disconnection monitoring...")
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """Stop camera disconnection monitoring"""
        self.is_monitoring = False
        LOGGER.info("Camera disconnection monitoring stopped")
        
    def _monitor_loop(self):
        """Main monitoring loop"""
        consecutive_failures = 0
        max_failures = 3  # Require 3 consecutive failures to confirm disconnect
        
        while self.is_monitoring:
            try:
                # Check camera availability
                camera_available = self._is_camera_available()
                
                if camera_available:
                    # Camera is connected
                    if not self.camera_connected:
                        LOGGER.info("Camera reconnected - canceling shutdown")
                        self._handle_camera_reconnected()
                    consecutive_failures = 0
                    
                else:
                    # Camera not detected
                    consecutive_failures += 1
                    
                    if consecutive_failures >= max_failures and self.camera_connected:
                        LOGGER.warning("Camera disconnection confirmed")
                        self._handle_camera_disconnected()
                    elif not self.camera_connected:
                        # Check if shutdown delay has elapsed
                        self._check_shutdown_timer()
                        
            except Exception as e:
                LOGGER.error(f"Error in camera monitoring: {e}")
                consecutive_failures += 1
                
            time.sleep(self.check_interval)
    
    def _is_camera_available(self):
        """Check if camera is available using platform-specific methods"""
        system = platform.system()
        detection_method = self.detection_methods.get(system)
        
        if detection_method:
            return detection_method()
        else:
            LOGGER.warning(f"No camera detection method for platform: {system}")
            return True  # Assume available if can't detect
    
    def _check_windows_camera(self):
        """Check camera availability on Windows"""
        try:
            # Method 1: Check Device Manager via PowerShell
            cmd = ['powershell', '-Command', 
                   "Get-PnpDevice -Class Camera | Where-Object {$_.Status -eq 'OK'}"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and result.stdout.strip():
                return True
                
            # Method 2: Check WMI
            cmd = ['wmic', 'path', 'Win32_USBHub', 'get', 'DeviceID', '/format:list']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            # Look for Intel RealSense camera identifiers
            realsense_ids = ['2AAD', '8086']  # Intel RealSense vendor IDs
            return any(vid_id in result.stdout for vid_id in realsense_ids)
            
        except Exception as e:
            LOGGER.debug(f"Windows camera check failed: {e}")
            return False
    
    def _check_linux_camera(self):
        """Check camera availability on Linux"""
        try:
            # Method 1: Check /dev/video* devices
            video_devices = [f'/dev/video{i}' for i in range(10)]
            if any(os.path.exists(device) for device in video_devices):
                return True
                
            # Method 2: Check USB devices
            try:
                with open('/proc/bus/usb/devices', 'r') as f:
                    usb_data = f.read()
                    # Look for Intel RealSense
                    return '8086' in usb_data or '2aad' in usb_data.lower()
            except:
                pass
                
            # Method 3: lsusb command
            result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=5)
            return 'Intel' in result.stdout and 'RealSense' in result.stdout
            
        except Exception as e:
            LOGGER.debug(f"Linux camera check failed: {e}")
            return False
    
    def _check_mac_camera(self):
        """Check camera availability on macOS"""
        try:
            # Check USB devices using system_profiler
            cmd = ['system_profiler', 'SPUSBDataType', '-xml']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            return 'Intel' in result.stdout and 'RealSense' in result.stdout
            
        except Exception as e:
            LOGGER.debug(f"macOS camera check failed: {e}")
            return False
    
    def _handle_camera_disconnected(self):
        """Handle camera disconnection event"""
        self.camera_connected = False
        self.disconnect_start_time = datetime.now()
        
        LOGGER.warning(f"Camera disconnected! Application will shutdown in {self.shutdown_delay} seconds")
        
        # Update UI to show disconnection
        self._notify_ui_camera_disconnected()
        
    def _handle_camera_reconnected(self):
        """Handle camera reconnection event"""
        self.camera_connected = True
        self.disconnect_start_time = None
        
        # Update UI to show reconnection
        self._notify_ui_camera_reconnected()
        
    def _check_shutdown_timer(self):
        """Check if shutdown delay has elapsed and trigger shutdown"""
        if self.disconnect_start_time:
            elapsed = datetime.now() - self.disconnect_start_time
            
            if elapsed.total_seconds() >= self.shutdown_delay:
                LOGGER.critical("Camera disconnect timeout reached - initiating application shutdown")
                self._trigger_shutdown()
    
    def _notify_ui_camera_disconnected(self):
        """Notify UI components about camera disconnection"""
        try:
            if hasattr(self.app, 'status_bar'):
                self.app.status_bar.set_msg(
                    f"⚠️ Camera Disconnected! App will close in {self.shutdown_delay}s", 
                    'warning'
                )
            
            # Update image feedback component
            if hasattr(self.app, 'image_feedback_frame'):
                self.app.image_feedback_frame.set_error_state("Camera Disconnected")
                
        except Exception as e:
            LOGGER.error(f"Failed to notify UI of camera disconnection: {e}")
    
    def _notify_ui_camera_reconnected(self):
        """Notify UI components about camera reconnection"""
        try:
            if hasattr(self.app, 'status_bar'):
                self.app.status_bar.set_msg("✅ Camera Reconnected", 'success')
                
        except Exception as e:
            LOGGER.error(f"Failed to notify UI of camera reconnection: {e}")
    
    def _trigger_shutdown(self):
        """Trigger application shutdown"""
        try:
            LOGGER.info("Triggering application shutdown due to camera disconnection...")
            
            # Show final message
            if hasattr(self.app, 'status_bar'):
                self.app.status_bar.set_msg("🔌 Camera disconnected - Shutting down...", 'danger')
            
            # Schedule shutdown on main thread
            if hasattr(self.app, 'after'):
                self.app.after(1000, self._perform_shutdown)
            else:
                self._perform_shutdown()
                
        except Exception as e:
            LOGGER.error(f"Error triggering shutdown: {e}")
            # Force exit if normal shutdown fails
            os._exit(1)
    
    def _perform_shutdown(self):
        """Perform the actual shutdown"""
        try:
            LOGGER.info("Performing application shutdown...")
            
            # Stop monitoring
            self.stop_monitoring()
            
            # Call application's exit method if available
            if hasattr(self.app, 'exit'):
                self.app.exit()
            else:
                # Force exit
                os._exit(0)
                
        except Exception as e:
            LOGGER.critical(f"Error during shutdown: {e}")
            os._exit(1)


# Enhanced Application Classes with Camera Monitoring

class AuthenticationApplicationWithMonitoring:
    """Enhanced AuthenticationApplication with camera disconnect monitoring"""
    
    def __init__(self, parent):
        # Initialize your existing application components first
        super().__init__(parent)
        
        # Initialize camera disconnect monitor
        self.camera_monitor = CameraDisconnectionMonitor(
            app_instance=self,
            shutdown_delay=15  # 15 seconds delay before shutdown
        )
        
        # Start monitoring after application is fully initialized
        self.after(5000, self._start_camera_monitoring)  # Start after 5 seconds
        
    def _start_camera_monitoring(self):
        """Start camera monitoring after application initialization"""
        try:
            self.camera_monitor.start_monitoring()
            LOGGER.info("Camera disconnection monitoring activated")
            
            # Show initial status
            if hasattr(self, 'status_bar'):
                self.status_bar.set_msg("📹 Camera monitoring active", 'info')
                
        except Exception as e:
            LOGGER.error(f"Failed to start camera monitoring: {e}")
    
    def exit(self):
        """Enhanced exit method that stops monitoring"""
        try:
            LOGGER.info('Application exiting with camera monitoring cleanup...')
            
            # Stop camera monitoring
            if hasattr(self, 'camera_monitor'):
                self.camera_monitor.stop_monitoring()
            
            # Send final status ping
            self._send_final_status_ping()
            
            # Exit application
            os._exit(0)
            
        except Exception as e:
            LOGGER.error(f"Error during exit: {e}")
            os._exit(1)
    
    def _send_final_status_ping(self):
        """Send final status ping before shutdown"""
        try:
            if hasattr(self, 'station_id'):
                from src.network_comms.database_handler import DatabaseHandler
                DatabaseHandler.send_app_status_ping(self.station_id)
                LOGGER.info("Final status ping sent")
        except Exception as e:
            LOGGER.error(f"Failed to send final status ping: {e}")


# Integration with existing application_authentication.py
class ModifiedAuthenticationApplication(AuthenticationApplicationWithMonitoring):
    """
    Modified version of your existing AuthenticationApplication
    Just replace the class definition in app_authentication.py with this one
    """
    
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent

        # ---Config initialization---
        self.config = _AppConfiguration()

        # ---Communication queues creation---
        self.cmd_request_q = queue.Queue()
        self.ready_status_q = queue.Queue()
        self.feedback_livestream_image_q = queue.Queue()
        self.feedback_livestream_detections_q = queue.Queue()
        self.feedback_msg_q = queue.Queue()
        self.faces_detected_feedback_q = queue.Queue()

        self.START_DELAY = 0

        # ---Generate unique station ID---
        self.station_id = self.generate_station_id()
        LOGGER.info(f"Station ID: {self.station_id}")

        # ---Initialize camera disconnect monitor EARLY---
        self.camera_monitor = CameraDisconnectionMonitor(
            app_instance=self,
            shutdown_delay=10  # 10 seconds delay
        )

        # ---Processor creation---
        self.socket_handler = SocketHandler()
        self.image_processor = ImageProcessor(
            self.feedback_livestream_image_q, self.feedback_livestream_detections_q, self.config
        )
        self.face_processor = FaceProcessor(
            self,
            self.cmd_request_q, self.ready_status_q,
            self.feedback_msg_q, self.faces_detected_feedback_q,
            self.feedback_livestream_detections_q, self.config,
            FaceProcessor.MODE_AUTHENTICATION, self.socket_handler
        )

        # ---Begin Processors---
        self.begin_processors()
        
        # ---Start App Status Heartbeat---
        self.start_app_status_heartbeat()

        # ---Internal GUI content creation---
        self.image_feedback_frame = ImageFeedback(self, self.config, self.feedback_livestream_image_q)
        self.image_feedback_frame.debug_color = "#00cc00"
        self.image_feedback_frame.pack(side=tk.TOP)

        self.status_bar = StatusBar(self, self.feedback_msg_q)
        self.status_bar.debug_color = "#33FFF3"
        self.status_bar.pack()

        self.cmd_interface_frame = CommandInterface(self, self.config, self.cmd_request_q, self.ready_status_q)
        self.cmd_interface_frame.debug_color = "#FF5733"
        self.cmd_interface_frame.pack()

        # ---Initialize window properties---
        self.init_window_properties()
        
        # ---Bind events---
        self.parent.bind('<<ON_IMAGE_FEEDBACK_SET>>', (lambda event: self.align_app_on_image_feedback_set()))
        self.parent.protocol("WM_DELETE_WINDOW", self.quit_app)
        
        # ---START CAMERA MONITORING (after full initialization)---
        self.after(3000, self._start_camera_monitoring)  # Start after 3 seconds

    def _start_camera_monitoring(self):
        """Start camera disconnect monitoring"""
        try:
            self.camera_monitor.start_monitoring()
            LOGGER.info("🔍 Camera disconnect monitoring started")
            
            # Update status bar
            self.status_bar.set_msg("📹 Camera monitoring active - will shutdown if disconnected")
            
        except Exception as e:
            LOGGER.error(f"Failed to start camera monitoring: {e}")

    def quit_app(self):
        """Modified quit app method"""
        self.status_bar.set_msg('Shutting down camera monitoring...')
        
        # Stop camera monitoring first
        if hasattr(self, 'camera_monitor'):
            self.camera_monitor.stop_monitoring()
            
        self.after(500, lambda: self.exit())

    # Keep all your existing methods (generate_station_id, begin_processors, etc.)
    # Just add the camera monitoring functionality


# Usage Instructions:
"""
INTEGRATION STEPS:

1. REPLACE YOUR EXISTING AuthenticationApplication CLASS:
   Replace the class definition in app_authentication.py with ModifiedAuthenticationApplication

2. ADD IMPORTS:
   Add these imports to the top of app_authentication.py:
   
   import platform
   import subprocess
   from datetime import datetime, timedelta

3. CONFIGURATION OPTIONS:
   You can customize the shutdown behavior by modifying:
   
   - shutdown_delay: Time to wait before shutdown (default: 10 seconds)
   - check_interval: How often to check camera (default: 2 seconds)
   - max_failures: Consecutive failures needed to confirm disconnect (default: 3)

4. TESTING:
   - Start the application normally
   - Wait for "Camera monitoring active" message
   - Unplug the camera USB cable
   - Application should detect disconnect and shutdown after the delay

5. LOGS:
   Monitor the logs for camera disconnection events:
   - "Camera disconnected! Application will shutdown in X seconds"
   - "Camera disconnect timeout reached - initiating application shutdown"
"""