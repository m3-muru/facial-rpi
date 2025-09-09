import os
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk_modern
from ttkbootstrap.constants import *
import queue
import time
import socket
import platform
import subprocess
from datetime import datetime, timedelta
import threading
from src.configuration.camera_monitor_config import CameraMonitorConfig, ConfigurableCameraDisconnectionMonitor

from src.configuration.app_authentication_config import _AppConfiguration
import src.utility.gui_window_utility as window_utility
from src.processor.image_processor import ImageProcessor
from src.processor.face_processor import FaceProcessor
from src.network_comms.socket_handler import SocketHandler
from src.network_comms.database_handler import DatabaseHandler

# Import modernized components
from src.GUI_authentication.modern_components.modern_image_feedback import ModernImageFeedback
from src.GUI_authentication.modern_components.modern_status_bar import ModernStatusBar
from src.GUI_authentication.modern_components.modern_command_interface import ModernCommandInterface
from src.GUI_authentication.modern_components.modern_header import ModernHeader
from src.GUI_authentication.modern_components.modern_system_panel import ModernSystemPanel

import src.logger.custom_logger as custom_logger
import webbrowser

LOGGER = custom_logger.get_logger()

# Try to import ETC monitoring with fallback
try:
    from src.network_comms.etc_connection_monitor import ETCConnectionMonitor
    ETC_MONITORING_AVAILABLE = True
    LOGGER.info("ETC connection monitoring available")
except ImportError as e:
    LOGGER.warning(f"ETC connection monitoring not available: {e}")
    ETC_MONITORING_AVAILABLE = False

# Modern color scheme
MODERN_COLORS = {
    'primary': '#2563EB',
    'secondary': '#64748B', 
    'success': '#10B981',
    'warning': '#F59E0B',
    'danger': '#EF4444',
    'info': '#06B6D4',
    'background': '#0F172A',
    'surface': '#1E293B',
    'surface_light': '#334155',
    'text_primary': '#F8FAFC',
    'text_secondary': '#CBD5E1',
    'accent': '#8B5CF6'
}

class CameraDisconnectionMonitor:
    """Monitors camera connection and triggers app shutdown on disconnect"""
    
    def __init__(self, app_instance, shutdown_delay=10):
        self.app = app_instance
        self.shutdown_delay = shutdown_delay
        self.is_monitoring = False
        self.camera_connected = True
        self.disconnect_start_time = None
        self.monitor_thread = None
        self.check_interval = 2
        
    def start_monitoring(self):
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        LOGGER.info("Starting camera disconnection monitoring...")
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        self.is_monitoring = False
        LOGGER.info("Camera disconnection monitoring stopped")
        
    def _monitor_loop(self):
        consecutive_failures = 0
        max_failures = 3
        
        while self.is_monitoring:
            try:
                camera_available = self._is_camera_available()
                
                if camera_available:
                    if not self.camera_connected:
                        LOGGER.info("Camera reconnected - canceling shutdown")
                        self._handle_camera_reconnected()
                    consecutive_failures = 0
                    
                else:
                    consecutive_failures += 1
                    
                    if consecutive_failures >= max_failures and self.camera_connected:
                        LOGGER.warning("Camera disconnection confirmed")
                        self._handle_camera_disconnected()
                    elif not self.camera_connected:
                        self._check_shutdown_timer()
                        
            except Exception as e:
                LOGGER.error(f"Error in camera monitoring: {e}")
                consecutive_failures += 1
                
            time.sleep(self.check_interval)
    
    def _is_camera_available(self):
        system = platform.system()
        
        if system == "Windows":
            return self._check_windows_camera()
        elif system == "Linux":
            return self._check_linux_camera()
        else:
            return True  # Assume available for other systems
    
    def _check_windows_camera(self):
        try:
            # Check Device Manager via PowerShell
            cmd = ['powershell', '-Command', 
                   "Get-PnpDevice -Class Camera | Where-Object {$_.Status -eq 'OK'}"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and result.stdout.strip():
                return True
                
            # Check USB devices for Intel RealSense
            cmd = ['wmic', 'path', 'Win32_USBHub', 'get', 'DeviceID', '/format:list']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            realsense_ids = ['2AAD', '8086']
            return any(vid_id in result.stdout for vid_id in realsense_ids)
            
        except Exception as e:
            LOGGER.debug(f"Windows camera check failed: {e}")
            return False
    
    def _check_linux_camera(self):
        try:
            # Check /dev/video* devices
            video_devices = [f'/dev/video{i}' for i in range(10)]
            if any(os.path.exists(device) for device in video_devices):
                return True
                
            # Check lsusb for Intel RealSense
            result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=5)
            return 'Intel' in result.stdout and ('RealSense' in result.stdout or '8086:' in result.stdout)
            
        except Exception as e:
            LOGGER.debug(f"Linux camera check failed: {e}")
            return False
    
    def _handle_camera_disconnected(self):
        self.camera_connected = False
        self.disconnect_start_time = datetime.now()
        
        LOGGER.warning(f"Camera disconnected! Application will shutdown in {self.shutdown_delay} seconds")
        
        try:
            if hasattr(self.app, 'status_bar'):
                self.app.status_bar.set_msg(
                    f"⚠️ Camera Disconnected! App will close in {self.shutdown_delay}s"
                )
            
            if hasattr(self.app, 'image_feedback_frame'):
                self.app.image_feedback_frame.set_error_state("Camera Disconnected - App Shutting Down")
                
        except Exception as e:
            LOGGER.error(f"Failed to notify UI of camera disconnection: {e}")
        
    def _handle_camera_reconnected(self):
        self.camera_connected = True
        self.disconnect_start_time = None
        
        try:
            if hasattr(self.app, 'status_bar'):
                self.app.status_bar.set_msg("✅ Camera Reconnected")
        except Exception as e:
            LOGGER.error(f"Failed to notify UI of camera reconnection: {e}")
        
    def _check_shutdown_timer(self):
        if self.disconnect_start_time:
            elapsed = datetime.now() - self.disconnect_start_time
            
            if elapsed.total_seconds() >= self.shutdown_delay:
                LOGGER.critical("Camera disconnect timeout reached - initiating application shutdown")
                self._trigger_shutdown()
    
    def _trigger_shutdown(self):
        try:
            LOGGER.info("Triggering application shutdown due to camera disconnection...")
            
            if hasattr(self.app, 'status_bar'):
                self.app.status_bar.set_msg("🔌 Camera disconnected - Shutting down...")
            
            if hasattr(self.app, 'after'):
                self.app.after(1000, self._perform_shutdown)
            else:
                self._perform_shutdown()
                
        except Exception as e:
            LOGGER.error(f"Error triggering shutdown: {e}")
            os._exit(1)
    
    def _perform_shutdown(self):
        try:
            LOGGER.info("Performing application shutdown...")
            self.stop_monitoring()
            
            if hasattr(self.app, 'exit'):
                self.app.exit()
            else:
                os._exit(0)
                
        except Exception as e:
            LOGGER.critical(f"Error during shutdown: {e}")
            os._exit(1)

class ModernAuthenticationApplication(ttk_modern.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.parent = parent
        self.setup_modern_theme()
        
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

        # ---Initialize camera disconnect monitor---
        self.camera_monitor = CameraDisconnectionMonitor(
            app_instance=self,
            shutdown_delay=15  # 15 seconds delay before shutdown
        )
        
        # ---Generate unique station ID---
        self.station_id = self.generate_station_id()
        LOGGER.info(f"Station ID: {self.station_id}")
        
        # ---Processor creation---
        self.socket_handler = SocketHandler()
        self.image_processor = ImageProcessor(
            self.feedback_livestream_image_q, 
            self.feedback_livestream_detections_q, 
            self.config
        )
        self.face_processor = FaceProcessor(
            self,
            self.cmd_request_q, 
            self.ready_status_q,
            self.feedback_msg_q, 
            self.faces_detected_feedback_q,
            self.feedback_livestream_detections_q, 
            self.config,
            FaceProcessor.MODE_AUTHENTICATION, 
            self.socket_handler
        )
        
        # ---Initialize modern UI components---
        self.init_single_column_scrollable_ui()
        
        # ---Begin Processors---
        self.begin_processors()
        
        # ---Start App Status Heartbeat---
        self.start_app_status_heartbeat()
        
        # ---Initialize ETC Monitoring---
        self.init_etc_monitoring()
        
        # ---Initialize window properties---
        self.init_modern_window_properties()
        
        # ---Bind events---
        self.bind_events()

        # ---START CAMERA MONITORING (after full initialization)---
        self.after(3000, self._start_camera_monitoring)  # Start after 3 seconds

    def setup_modern_theme(self):
        """Setup modern dark theme"""
        try:
            # Use a modern dark theme
            self.style = ttk_modern.Style("superhero")  # Dark theme
            
            # Configure custom styles
            self.style.configure('Modern.TFrame', background=MODERN_COLORS['surface'])
            self.style.configure('Header.TFrame', background=MODERN_COLORS['background'])
            self.style.configure('Surface.TFrame', background=MODERN_COLORS['surface_light'])
            self.style.configure('ScrollableFrame.TFrame', background=MODERN_COLORS['background'])
            
            self.style.configure('Modern.TLabel', 
                               background=MODERN_COLORS['surface'],
                               foreground=MODERN_COLORS['text_primary'],
                               font=('Segoe UI', 10))
            
            self.style.configure('Title.TLabel',
                               background=MODERN_COLORS['background'],
                               foreground=MODERN_COLORS['text_primary'],
                               font=('Segoe UI', 16, 'bold'))
            
            self.style.configure('Subtitle.TLabel',
                               background=MODERN_COLORS['background'],
                               foreground=MODERN_COLORS['text_secondary'],
                               font=('Segoe UI', 9))
                               
        except Exception as e:
            LOGGER.warning(f"Failed to setup modern theme: {e}")
            # Fallback to default theme
            self.style = ttk.Style()

    def init_single_column_scrollable_ui(self):
        """Initialize single column scrollable UI layout"""
        # Configure main frame
        self.configure(style='Modern.TFrame')
        
        # Create main container
        main_container = ttk_modern.Frame(self, style='Modern.TFrame')
        main_container.pack(fill=BOTH, expand=True)
        
        # Create scrollable frame container
        self.create_scrollable_container(main_container)
    
    def _start_camera_monitoring(self):
        """Start camera disconnect monitoring"""
        try:
            self.camera_monitor.start_monitoring()
            LOGGER.info("🔍 Camera disconnect monitoring started - app will shutdown if camera disconnected")
            
            # Update status bar
            self.send_feedback_msg("📹 Camera monitoring active", FaceDetectionStatus.ACCEPTED)
            
        except Exception as e:
            LOGGER.error(f"Failed to start camera monitoring: {e}")

    def send_feedback_msg(self, msg='Warning: missing feedback msg', face_process_status=None):
        """Helper method to send feedback messages"""
        self.feedback_msg_q.put(
            {
                "msg": msg,
                "status": face_process_status
            }
        )

    def create_scrollable_container(self, parent):
        """Create scrollable container for all content"""
        # Create canvas and scrollbar for scrolling
        canvas_frame = ttk_modern.Frame(parent, style='ScrollableFrame.TFrame')
        canvas_frame.pack(fill=BOTH, expand=True, padx=3, pady=3)
        
        # Canvas for scrollable content
        self.canvas = tk.Canvas(
            canvas_frame,
            bg=MODERN_COLORS['background'],
            highlightthickness=0,
            relief='flat'
        )
        
        # Scrollbar
        scrollbar = ttk_modern.Scrollbar(
            canvas_frame,
            orient="vertical",
            command=self.canvas.yview,
            style='primary.Vertical.TScrollbar'
        )
        
        # Scrollable frame inside canvas
        self.scrollable_frame = ttk_modern.Frame(self.canvas, style='ScrollableFrame.TFrame')
        
        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Create window in canvas
        self.canvas_window = self.canvas.create_window(
            (0, 0), 
            window=self.scrollable_frame, 
            anchor="nw"
        )
        
        # Configure canvas scrolling
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        self.bind_mousewheel()
        
        # Bind canvas resize
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        
        # Now create all content in the scrollable frame
        self.create_single_column_content()

    def bind_mousewheel(self):
        """Bind mousewheel events for scrolling"""
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")
        
        # Bind when mouse enters canvas
        self.canvas.bind('<Enter>', _bind_to_mousewheel)
        self.canvas.bind('<Leave>', _unbind_from_mousewheel)

    def on_canvas_configure(self, event):
        """Handle canvas resize to make scrollable frame fit width"""
        # Update the scrollable frame width to match canvas width
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def create_single_column_content(self):
        """Create all content in single column layout optimized for 400px width"""
        # Add padding to the main content
        content_container = ttk_modern.Frame(self.scrollable_frame, style='ScrollableFrame.TFrame')
        content_container.pack(fill=BOTH, expand=True, padx=8, pady=8)
        
        # 1. Camera feed section
        camera_section = self.create_section_container(
            content_container, 
            "📹 Live Camera Feed"
        )
        
        self.image_feedback_frame = ModernImageFeedback(
            camera_section, 
            self.config, 
            self.feedback_livestream_image_q
        )
        self.image_feedback_frame.pack(fill=X, pady=(0, 10))
        
        # 2. Hidden command interface for background processing
        hidden_frame = ttk_modern.Frame(content_container, style='ScrollableFrame.TFrame')
        # Don't pack the hidden_frame - it won't be visible
        
        self.cmd_interface_frame = ModernCommandInterface(
            hidden_frame, 
            self.config, 
            self.cmd_request_q, 
            self.ready_status_q
        )
        
        # 3. Status section
        status_section = self.create_section_container(
            content_container,
            "🔄 System Status"
        )
        
        self.status_frame = ModernStatusBar(status_section, self.feedback_msg_q)
        self.status_frame.pack(fill=X, pady=(0, 10))
        
        # 4. System information section
        system_section = self.create_section_container(
            content_container,
            "💻 System Info"
        )
        
        self.system_panel = ModernSystemPanel(system_section, self.config)
        self.system_panel.pack(fill=X, pady=(0, 10))
        
        # 5. ETC Connection Status section
        # self.create_etc_section(content_container)
        
        # 6. Footer section
        # self.init_footer(content_container)
        
        # Add bottom padding for better scrolling
        bottom_spacer = ttk_modern.Frame(content_container, style='ScrollableFrame.TFrame', height=30)
        bottom_spacer.pack(fill=X)

    def create_etc_section(self, parent):
        """Create ETC connection monitoring section"""
        try:
            if ETC_MONITORING_AVAILABLE:
                etc_section = self.create_section_container(
                    parent,
                    " ETC Connection"
                )
                self.create_etc_status_display(etc_section)
            else:
                # Create placeholder section
                etc_section = self.create_section_container(
                    parent,
                    " ETC Connection"
                )
                self.create_etc_unavailable_display(etc_section)
                
        except Exception as e:
            LOGGER.error(f"Failed to create ETC section: {e}")
            # Create error display
            try:
                etc_section = self.create_section_container(
                    parent,
                    " ETC Connection"
                )
                self.create_etc_error_display(etc_section, str(e))
            except:
                LOGGER.error("Failed to create ETC error display")

    def create_etc_status_display(self, parent):
        """Create ETC status display"""
        try:
            # Main container
            status_container = tk.Frame(
                parent, 
                bg=MODERN_COLORS['surface_light'], 
                height=45,
                relief='flat'
            )
            status_container.pack(fill=X, padx=5, pady=5)
            status_container.pack_propagate(False)
            
            # Left side - Status info
            left_frame = tk.Frame(status_container, bg=MODERN_COLORS['surface_light'])
            left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 0))
            
            # Status dot
            self.etc_status_dot = tk.Label(
                left_frame,
                text="●",
                font=('Segoe UI', 12),
                bg=MODERN_COLORS['surface_light'],
                fg=MODERN_COLORS['warning']
            )
            self.etc_status_dot.pack(side=tk.LEFT, pady=12)
            
            # Status text
            self.etc_status_text = tk.Label(
                left_frame,
                text="ETC: Initializing...",
                font=('Segoe UI', 10, 'bold'),
                bg=MODERN_COLORS['surface_light'],
                fg=MODERN_COLORS['text_primary']
            )
            self.etc_status_text.pack(side=tk.LEFT, padx=(5, 0), pady=12)
            
            # Right side - Action buttons
            right_frame = tk.Frame(status_container, bg=MODERN_COLORS['surface_light'])
            right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10))
            
            # Test button
            self.etc_test_btn = tk.Button(
                right_frame,
                text="🔄",
                font=('Segoe UI', 9),
                bg=MODERN_COLORS['info'],
                fg='white',
                relief='flat',
                bd=0,
                width=3,
                height=1,
                command=self.test_etc_connection_safe
            )
            self.etc_test_btn.pack(side=tk.RIGHT, padx=(3, 0), pady=10)
            
            # Open ETC button
            self.etc_open_btn = tk.Button(
                right_frame,
                text="",
                font=('Segoe UI', 9),
                bg=MODERN_COLORS['primary'],
                fg='white',
                relief='flat',
                bd=0,
                width=3,
                height=1,
                command=self.open_etc_page_safe
            )
            self.etc_open_btn.pack(side=tk.RIGHT, padx=(3, 0), pady=10)
            
            LOGGER.debug("ETC status display created successfully")
            
        except Exception as e:
            LOGGER.error(f"Error creating ETC status display: {e}")
            self.create_etc_error_display(parent, "Display Error")

    def create_etc_unavailable_display(self, parent):
        """Create display when ETC monitoring is unavailable"""
        unavailable_frame = tk.Frame(
            parent, 
            bg=MODERN_COLORS['surface_light'], 
            height=35
        )
        unavailable_frame.pack(fill=X, padx=5, pady=5)
        unavailable_frame.pack_propagate(False)
        
        unavailable_label = tk.Label(
            unavailable_frame,
            text="⚠️ ETC Monitoring Not Available",
            font=('Segoe UI', 9),
            bg=MODERN_COLORS['surface_light'],
            fg=MODERN_COLORS['warning']
        )
        unavailable_label.pack(pady=8)

    def create_etc_error_display(self, parent, error_msg):
        """Create error display for ETC monitoring"""
        error_frame = tk.Frame(
            parent, 
            bg=MODERN_COLORS['surface_light'], 
            height=35
        )
        error_frame.pack(fill=X, padx=5, pady=5)
        error_frame.pack_propagate(False)
        
        error_label = tk.Label(
            error_frame,
            text=f"🔴 ETC Error: {error_msg[:30]}...",
            font=('Segoe UI', 9),
            bg=MODERN_COLORS['surface_light'],
            fg=MODERN_COLORS['danger']
        )
        error_label.pack(pady=8)

    def init_etc_monitoring(self):
        """Initialize ETC connection monitoring"""
        if not ETC_MONITORING_AVAILABLE:
            LOGGER.info("ETC monitoring not available, skipping initialization")
            return
            
        try:
            # Create ETC monitor
            self.etc_monitor = ETCConnectionMonitor("http://localhost:8080")
            
            # Add status callback
            self.etc_monitor.add_status_callback(self.on_etc_status_change)
            
            # Start monitoring
            self.etc_monitor.start_monitoring()
            
            # Test connection in background
            def initial_test():
                time.sleep(2)  # Wait for UI to be ready
                self.etc_monitor.test_connection_now()
            
            threading.Thread(target=initial_test, daemon=True).start()
            
            LOGGER.info("ETC monitoring initialized successfully")
            
        except Exception as e:
            LOGGER.error(f"Failed to initialize ETC monitoring: {e}")
            self.etc_monitor = None

    def on_etc_status_change(self, status_type, is_connected, details=None):
        """Handle ETC connection status changes"""
        try:
            # Schedule UI update on main thread
            self.after_idle(lambda: self.update_etc_status_display())
            
            # Also update status bar
            if hasattr(self, 'status_frame') and self.status_frame:
                if status_type == "etc_web":
                    if is_connected:
                        self.after_idle(lambda: self.status_frame.set_msg(" ETC Web Connected", "success"))
                    else:
                        self.after_idle(lambda: self.status_frame.set_msg(" ETC Web Disconnected", "danger"))
                elif status_type == "websocket":
                    if is_connected:
                        self.after_idle(lambda: self.status_frame.set_msg(" ETC WebSocket Connected", "success"))
                    else:
                        self.after_idle(lambda: self.status_frame.set_msg("⚠️ ETC WebSocket Issue", "warning"))
                        
        except Exception as e:
            LOGGER.error(f"Error in ETC status callback: {e}")

    def update_etc_status_display(self):
        """Update ETC status display"""
        try:
            if not hasattr(self, 'etc_monitor') or not self.etc_monitor:
                return
                
            if not hasattr(self, 'etc_status_dot') or not hasattr(self, 'etc_status_text'):
                return
                
            # Get current status
            status = self.etc_monitor.get_connection_status()
            overall = status.get('overall_status', 'disconnected')
            
            # Update display based on overall status
            if overall == "fully_connected":
                self.etc_status_dot.configure(fg=MODERN_COLORS['success'])
                self.etc_status_text.configure(
                    text="ETC: Connected ✓",
                    fg=MODERN_COLORS['success']
                )
            elif overall == "partially_connected":
                self.etc_status_dot.configure(fg=MODERN_COLORS['warning'])
                self.etc_status_text.configure(
                    text="ETC: Partial ⚠",
                    fg=MODERN_COLORS['warning']
                )
            else:
                self.etc_status_dot.configure(fg=MODERN_COLORS['danger'])
                self.etc_status_text.configure(
                    text="ETC: Disconnected ✗",
                    fg=MODERN_COLORS['danger']
                )
                
            LOGGER.debug(f"ETC status updated: {overall}")
            
        except Exception as e:
            LOGGER.error(f"Error updating ETC status display: {e}")

    def test_etc_connection_safe(self):
        """Safely test ETC connection"""
        try:
            if not hasattr(self, 'etc_monitor') or not self.etc_monitor:
                LOGGER.warning("No ETC monitor available for testing")
                return
                
            # Update button state
            if hasattr(self, 'etc_test_btn'):
                self.etc_test_btn.configure(text="⏳", state="disabled")
            
            # Update status text
            if hasattr(self, 'etc_status_text'):
                self.etc_status_text.configure(text="ETC: Testing...")
            
            def run_test():
                try:
                    self.etc_monitor.test_connection_now()
                finally:
                    # Restore button on main thread
                    self.after_idle(self.restore_test_button)
            
            # Run test in background
            threading.Thread(target=run_test, daemon=True).start()
            
        except Exception as e:
            LOGGER.error(f"Error in test_etc_connection_safe: {e}")
            self.restore_test_button()

    def restore_test_button(self):
        """Restore test button to normal state"""
        try:
            if hasattr(self, 'etc_test_btn'):
                self.etc_test_btn.configure(text="🔄", state="normal")
        except Exception as e:
            LOGGER.error(f"Error restoring test button: {e}")

    def open_etc_page_safe(self):
        """Safely open ETC page"""
        try:
            if hasattr(self, 'etc_monitor') and self.etc_monitor:
                etc_url = self.etc_monitor.etc_full_url
            else:
                etc_url = "http://localhost:8080/psms/mcs/ETC.xhtml?mode=facial&inout=O"
            
            webbrowser.open(etc_url)
            LOGGER.info(f"Opening ETC page: {etc_url}")
            
            # Update status text briefly
            if hasattr(self, 'etc_status_text'):
                original_text = self.etc_status_text.cget('text')
                self.etc_status_text.configure(text="ETC: Opening...")
                self.after(2000, lambda: self.etc_status_text.configure(text=original_text))
                
        except Exception as e:
            LOGGER.error(f"Error opening ETC page: {e}")

    def create_section_container(self, parent, title):
        """Create a section container with title"""
        # Section frame
        section_frame = ttk_modern.Frame(parent, style='Surface.TFrame')
        section_frame.pack(fill=X, pady=(0, 10))
        
        if title:  # Only create header if title is provided
            # Section header
            header_frame = tk.Frame(
                section_frame,
                bg=MODERN_COLORS['surface_light'],
                height=35
            )
            header_frame.pack(fill=X, padx=1, pady=1)
            header_frame.pack_propagate(False)
            
            # Title
            title_label = tk.Label(
                header_frame,
                text=title,
                font=('Segoe UI', 10, 'bold'),
                bg=MODERN_COLORS['surface_light'],
                fg=MODERN_COLORS['text_primary'],
                anchor='w'
            )
            title_label.pack(side=LEFT, fill=Y, padx=10, pady=6)
        
        # Content container
        content_frame = ttk_modern.Frame(section_frame, style='Surface.TFrame')
        content_frame.pack(fill=X, padx=1, pady=(0, 1))
        
        return content_frame

    def init_footer(self, parent):
        """Initialize compact footer"""
        footer_frame = tk.Frame(
            parent, 
            bg=MODERN_COLORS['surface_light'],
            height=50
        )
        footer_frame.pack(fill=X, pady=(15, 0))
        footer_frame.pack_propagate(False)
        
        # Footer content
        footer_content = tk.Frame(footer_frame, bg=MODERN_COLORS['surface_light'])
        footer_content.pack(fill=BOTH, expand=True, padx=10, pady=8)
        
        # Left side - Status indicators
        left_footer = tk.Frame(footer_content, bg=MODERN_COLORS['surface_light'])
        left_footer.pack(side=LEFT, fill=Y)
        
        status_row = tk.Frame(left_footer, bg=MODERN_COLORS['surface_light'])
        status_row.pack(fill=X)
        
        status_indicators = [
            ("DB", "●", MODERN_COLORS['success']),
            ("CAM", "●", MODERN_COLORS['success']),
            ("NET", "●", MODERN_COLORS['success']),
            ("AI", "●", MODERN_COLORS['success'])
        ]
        
        for name, indicator, color in status_indicators:
            self.create_compact_status_indicator(status_row, name, indicator, color)
        
        # Right side - Version and time
        right_footer = tk.Frame(footer_content, bg=MODERN_COLORS['surface_light'])
        right_footer.pack(side=RIGHT, fill=Y)
        
        version_label = tk.Label(
            right_footer,
            text="v2.0.0",
            font=('Segoe UI', 8, 'bold'),
            bg=MODERN_COLORS['surface_light'],
            fg=MODERN_COLORS['text_primary']
        )
        version_label.pack(anchor='e')
        
        self.time_label = tk.Label(
            right_footer,
            text="",
            font=('Segoe UI', 7),
            bg=MODERN_COLORS['surface_light'],
            fg=MODERN_COLORS['text_secondary']
        )
        self.time_label.pack(anchor='e', pady=(3, 0))
        
        # Start time update
        self.update_time()

    def create_compact_status_indicator(self, parent, name, indicator, color):
        """Create a compact status indicator"""
        indicator_frame = tk.Frame(parent, bg=MODERN_COLORS['surface_light'])
        indicator_frame.pack(side=LEFT, padx=(0, 8))
        
        dot_label = tk.Label(
            indicator_frame, 
            text=indicator,
            foreground=color,
            background=MODERN_COLORS['surface_light'],
            font=('Segoe UI', 8)
        )
        dot_label.pack(side=LEFT, padx=(0, 3))
        
        text_label = tk.Label(
            indicator_frame,
            text=name,
            font=('Segoe UI', 7),
            bg=MODERN_COLORS['surface_light'],
            fg=MODERN_COLORS['text_secondary']
        )
        text_label.pack(side=LEFT)

    def update_time(self):
        """Update time display"""
        current_time = datetime.now().strftime("%H:%M:%S")
        current_date = datetime.now().strftime("%m-%d")
        self.time_label.configure(text=f"{current_date} {current_time}")
        self.after(1000, self.update_time)

    def scroll_to_top(self):
        """Scroll to top of the interface"""
        self.canvas.yview_moveto(0)

    def generate_station_id(self):
        """Generate a unique station ID"""
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            station_id = f"ETC_{hostname}_{local_ip.replace('.', '_')}"
            return station_id
        except Exception as e:
            LOGGER.error(f"Error generating station ID: {e}")
            return "ETC_UNKNOWN_STATION"

    def start_app_status_heartbeat(self):
        """Start sending regular status pings to the server"""
        try:
            DatabaseHandler.send_app_status_ping(self.station_id)
            DatabaseHandler.init_app_status_heartbeat(self.station_id, interval_seconds=60)
            LOGGER.info("App status heartbeat initialized successfully")
        except Exception as e:
            LOGGER.error(f"Failed to initialize app status heartbeat: {e}")

    def begin_processors(self):
        """Start all processors"""
        self.begin_web_socket_server()
        time.sleep(self.START_DELAY)
        self.begin_image_processing()
        self.begin_face_processing()

    def begin_image_processing(self):
        self.image_processor.start()

    def begin_face_processing(self):
        self.face_processor.start()

    def begin_web_socket_server(self):
        self.socket_handler.start()

    def init_modern_window_properties(self):
        """Initialize modern window properties"""
        self.parent.title(f'ENVIS Face Recognition - {self.station_id}')
        self.parent.configure(bg=MODERN_COLORS['background'])
        
        # Set window size to exactly 400px width
        self.parent.minsize(400, 600)
        self.parent.maxsize(400, 1200)
        
        # Set initial size
        self.parent.geometry("400x950")
        
        # Disable horizontal resizing
        self.parent.resizable(False, True)
        
        # Always on top
        self.parent.attributes("-topmost", True)
        
        # Position at top right
        self.position_window_top_right()

    def position_window_top_right(self):
        """Position window at top right corner"""
        self.parent.update_idletasks()
        
        screen_width = self.parent.winfo_screenwidth()
        window_width = self.parent.winfo_width()
        
        margin = 10
        x_position = screen_width - window_width - margin
        y_position = margin
        
        self.parent.geometry(f"{window_width}x{self.parent.winfo_height()}+{x_position}+{y_position}")
        LOGGER.info(f"Window positioned at top right: {x_position}, {y_position}")

    def bind_events(self):
        """Bind keyboard and window events"""
        # Keyboard shortcuts
        self.parent.bind('<F1>', lambda event: self.scroll_to_top())
        self.parent.bind('<F2>', lambda event: window_utility.align_window(
            self.parent, window_utility.ALIGN_TOP_RIGHT))
        self.parent.bind('<F3>', lambda event: window_utility.print_window_properties(self.parent))
        self.parent.bind('<Escape>', lambda event: self.quit_app())
        self.parent.bind('<Home>', lambda event: self.scroll_to_top())
        self.parent.bind('<End>', lambda event: self.canvas.yview_moveto(1))
        
        # Page up/down for scrolling
        self.parent.bind('<Prior>', lambda event: self.canvas.yview_scroll(-1, "pages"))
        self.parent.bind('<Next>', lambda event: self.canvas.yview_scroll(1, "pages"))
        
        # Arrow keys for scrolling
        self.parent.bind('<Up>', lambda event: self.canvas.yview_scroll(-1, "units"))
        self.parent.bind('<Down>', lambda event: self.canvas.yview_scroll(1, "units"))
        
        # Window events
        self.parent.bind('<<ON_IMAGE_FEEDBACK_SET>>', 
                        lambda event: self.align_app_on_image_feedback_set())
        self.parent.protocol("WM_DELETE_WINDOW", self.quit_app)

    def align_app_on_image_feedback_set(self):
        """Align app when image feedback is set"""
        LOGGER.debug('<<ON_IMAGE_FEEDBACK_SET>>')
        self.parent.unbind('<<ON_IMAGE_FEEDBACK_SET>>')
        window_utility.align_window(self.parent, window_utility.ALIGN_TOP_RIGHT)
        self.parent.event_generate("<<ON_APP_ALIGNED>>")

    def quit_app(self):
        self.send_feedback_msg('Shutting down camera monitoring...')
        
        # Stop camera monitoring first
        if hasattr(self, 'camera_monitor'):
            self.camera_monitor.stop_monitoring()
            
        self.after(500, lambda: self.exit())

    def exit(self):
        import os
        LOGGER.info(f'Application exiting with camera monitoring cleanup...')
        
        # Stop camera monitoring
        if hasattr(self, 'camera_monitor'):
            self.camera_monitor.stop_monitoring()
        
        # Send final status ping before exit
        try:
            import datetime
            final_status = {
                "station_id": self.station_id,
                "hostname": socket.gethostname(),
                "ip_address": socket.gethostbyname(socket.gethostname()),
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "shutting_down_camera_disconnect",
                "app_version": "1.0.0",
                "last_ping": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            DatabaseHandler.send_app_status_ping(self.station_id)
            LOGGER.info("Final status ping sent")
        except Exception as e:
            LOGGER.error(f"Failed to send final status ping: {e}")
        
        os._exit(0)


def main():
    """Main entry point"""
    LOGGER.info('Modern 400px Width Application starting...')
    
    # Create main window with modern styling and 400px width
    root = ttk_modern.Window(
        title="ENVIS Face Recognition System",
        themename="superhero",  # Modern dark theme
        size=(400, 800),  # Fixed width of 400px
        resizable=(False, True)  # Disable horizontal resizing
    )
    
    # Apply additional window styling
    root.configure(bg=MODERN_COLORS['background'])
    
    # Set window constraints to maintain 400px width
    root.minsize(400, 600)
    root.maxsize(400, 1200)
    
    # Create and pack the application
    app = ModernAuthenticationApplication(root)
    app.pack(side="top", fill="both", expand=True)
    
    # Open web browser
    webbrowser.open("http://localhost:8080/psms/mcs/ETC.xhtml?mode=facial&inout=O")
    # webbrowser.open("https://envis.stengglink.com/psms/mcs/ETC.xhtml?mode=facial&inout=I")
    #
    
    # Start the application
    root.mainloop()


if __name__ == "__main__":
    main()