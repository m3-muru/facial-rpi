import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk_modern
from ttkbootstrap.constants import *
from datetime import datetime
import socket
import src.logger.custom_logger as custom_logger

LOGGER = custom_logger.get_logger()

# Modern color scheme
MODERN_COLORS = {
    'primary': '#2563EB',
    'secondary': '#64748B',
    'success': '#10B981',
    'warning': '#F59E0B',
    'danger': '#EF4444',
    'background': '#0F172A',
    'surface': '#1E293B',
    'surface_light': '#334155',
    'text_primary': '#F8FAFC',
    'text_secondary': '#CBD5E1',
    'accent': '#8B5CF6'
}

class ModernHeader(ttk_modern.Frame):
    def __init__(self, parent, station_id, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.parent = parent
        self.station_id = station_id
        
        # Network status tracking
        self.network_status = "connected"
        self.last_ping_time = datetime.now()
        
        self.init_modern_ui()
        self.start_status_updates()

    def init_modern_ui(self):
        """Initialize modern header UI"""
        # Configure the header frame
        self.configure(style='Header.TFrame')
        
        # Main header container with gradient effect simulation
        header_container = tk.Frame(
            self,
            bg=MODERN_COLORS['background'],
            height=80,
            relief='flat',
            bd=0
        )
        header_container.pack(fill=BOTH, expand=True, padx=0, pady=0)
        header_container.pack_propagate(False)
        
        # Left section - Logo and title
        left_section = tk.Frame(header_container, bg=MODERN_COLORS['background'])
        left_section.pack(side=LEFT, fill=Y, padx=20, pady=15)
        
        self.init_logo_section(left_section)
        
        # Center section - System status
        center_section = tk.Frame(header_container, bg=MODERN_COLORS['background'])
        center_section.pack(side=LEFT, fill=BOTH, expand=True, padx=20)
        
        self.init_status_section(center_section)
        
        # Right section - Time, network, and controls
        right_section = tk.Frame(header_container, bg=MODERN_COLORS['background'])
        right_section.pack(side=RIGHT, fill=Y, padx=20, pady=15)
        
        self.init_info_section(right_section)

    def init_logo_section(self, parent):
        """Initialize logo and title section"""
        # Logo placeholder (you can replace with actual logo)
        logo_frame = tk.Frame(parent, bg=MODERN_COLORS['primary'], width=50, height=50)
        logo_frame.pack(side=LEFT, padx=(0, 15))
        logo_frame.pack_propagate(False)
        
        # Logo icon
        logo_label = tk.Label(
            logo_frame,
            text="🛡️",
            font=('Segoe UI', 20),
            bg=MODERN_COLORS['primary'],
            fg='white'
        )
        logo_label.pack(expand=True)
        
        # Title and subtitle
        title_frame = tk.Frame(parent, bg=MODERN_COLORS['background'])
        title_frame.pack(side=LEFT, fill=Y)
        
        # Main title
        title_label = tk.Label(
            title_frame,
            text="ENVIS Face Recognition",
            font=('Segoe UI', 18, 'bold'),
            bg=MODERN_COLORS['background'],
            fg=MODERN_COLORS['text_primary'],
            anchor='w'
        )
        title_label.pack(anchor='w')
        
        # Subtitle
        subtitle_label = tk.Label(
            title_frame,
            text="Enterprise Time & Attendance System",
            font=('Segoe UI', 10),
            bg=MODERN_COLORS['background'],
            fg=MODERN_COLORS['text_secondary'],
            anchor='w'
        )
        subtitle_label.pack(anchor='w')

    def init_status_section(self, parent):
        """Initialize center status section"""
        # Station ID display
        station_frame = tk.Frame(parent, bg=MODERN_COLORS['background'])
        station_frame.pack(expand=True, fill='both')
        
        # Station ID with modern styling
        station_container = tk.Frame(
            station_frame,
            bg=MODERN_COLORS['surface'],
            relief='flat',
            bd=0,
            highlightbackground=MODERN_COLORS['surface_light'],
            highlightthickness=1
        )
        station_container.pack(expand=True, pady=10)
        
        station_content = tk.Frame(station_container, bg=MODERN_COLORS['surface'])
        station_content.pack(fill=BOTH, expand=True, padx=15, pady=8)
        
        # Station icon and text
        station_icon = tk.Label(
            station_content,
            text="🏢",
            font=('Segoe UI', 14),
            bg=MODERN_COLORS['surface'],
            fg=MODERN_COLORS['accent']
        )
        station_icon.pack(side=LEFT, padx=(0, 10))
        
        station_info_frame = tk.Frame(station_content, bg=MODERN_COLORS['surface'])
        station_info_frame.pack(side=LEFT, fill=X, expand=True)
        
        station_label = tk.Label(
            station_info_frame,
            text="Station ID",
            font=('Segoe UI', 8),
            bg=MODERN_COLORS['surface'],
            fg=MODERN_COLORS['text_secondary'],
            anchor='w'
        )
        station_label.pack(anchor='w')
        
        self.station_id_label = tk.Label(
            station_info_frame,
            text=self.station_id,
            font=('Segoe UI', 11, 'bold'),
            bg=MODERN_COLORS['surface'],
            fg=MODERN_COLORS['text_primary'],
            anchor='w'
        )
        self.station_id_label.pack(anchor='w')

    def init_info_section(self, parent):
        """Initialize right info section"""
        # Time display
        time_frame = tk.Frame(parent, bg=MODERN_COLORS['background'])
        time_frame.pack(side=RIGHT, padx=(15, 0))
        
        # Current time
        self.time_label = tk.Label(
            time_frame,
            text="",
            font=('Segoe UI', 16, 'bold'),
            bg=MODERN_COLORS['background'],
            fg=MODERN_COLORS['text_primary'],
            anchor='e'
        )
        self.time_label.pack(anchor='e')
        
        # Current date
        self.date_label = tk.Label(
            time_frame,
            text="",
            font=('Segoe UI', 10),
            bg=MODERN_COLORS['background'],
            fg=MODERN_COLORS['text_secondary'],
            anchor='e'
        )
        self.date_label.pack(anchor='e')
        
        # System indicators
        indicators_frame = tk.Frame(parent, bg=MODERN_COLORS['background'])
        indicators_frame.pack(side=RIGHT, padx=(15, 0))
        
        self.init_system_indicators(indicators_frame)

    def init_system_indicators(self, parent):
        """Initialize system status indicators"""
        # Network status
        self.network_frame = tk.Frame(parent, bg=MODERN_COLORS['background'])
        self.network_frame.pack(pady=(0, 5))
        
        self.network_icon = tk.Label(
            self.network_frame,
            text="📶",
            font=('Segoe UI', 12),
            bg=MODERN_COLORS['background'],
            fg=MODERN_COLORS['success']
        )
        self.network_icon.pack(side=LEFT, padx=(0, 5))
        
        self.network_label = tk.Label(
            self.network_frame,
            text="Connected",
            font=('Segoe UI', 9),
            bg=MODERN_COLORS['background'],
            fg=MODERN_COLORS['text_secondary']
        )
        self.network_label.pack(side=LEFT)
        
        # Host info
        host_frame = tk.Frame(parent, bg=MODERN_COLORS['background'])
        host_frame.pack()
        
        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            
            host_label = tk.Label(
                host_frame,
                text=f"💻 {hostname}",
                font=('Segoe UI', 8),
                bg=MODERN_COLORS['background'],
                fg=MODERN_COLORS['text_secondary'],
                anchor='e'
            )
            host_label.pack(anchor='e')
            
            ip_label = tk.Label(
                host_frame,
                text=f" {ip_address}",
                font=('Segoe UI', 8),
                bg=MODERN_COLORS['background'],
                fg=MODERN_COLORS['text_secondary'],
                anchor='e'
            )
            ip_label.pack(anchor='e')
            
        except Exception as e:
            LOGGER.warning(f"Failed to get host info: {e}")

    def update_time_display(self):
        """Update time and date display"""
        now = datetime.now()
        
        # Update time
        time_str = now.strftime("%H:%M:%S")
        self.time_label.configure(text=time_str)
        
        # Update date
        date_str = now.strftime("%A, %B %d, %Y")
        self.date_label.configure(text=date_str)

    def update_network_status(self, status="connected", message="Connected"):
        """Update network status indicator"""
        self.network_status = status
        
        status_configs = {
            "connected": {
                "icon": "📶",
                "color": MODERN_COLORS['success'],
                "text": message
            },
            "disconnected": {
                "icon": "📵",
                "color": MODERN_COLORS['danger'],
                "text": "Offline"
            },
            "warning": {
                "icon": "⚠️",
                "color": MODERN_COLORS['warning'],
                "text": message
            }
        }
        
        config = status_configs.get(status, status_configs["connected"])
        
        self.network_icon.configure(
            text=config["icon"],
            fg=config["color"]
        )
        
        self.network_label.configure(
            text=config["text"],
            fg=config["color"] if status != "connected" else MODERN_COLORS['text_secondary']
        )

    def pulse_network_indicator(self):
        """Pulse network indicator for activity"""
        original_size = 12
        
        def pulse():
            for size in [14, 12]:
                self.network_icon.configure(font=('Segoe UI', size))
                self.update()
                self.after(100)
        
        pulse()

    def show_notification(self, message, notification_type="info", duration=3000):
        """Show a temporary notification in the header"""
        # Create notification overlay
        notification_frame = tk.Frame(
            self,
            bg=MODERN_COLORS['primary'] if notification_type == "info" else 
               MODERN_COLORS['success'] if notification_type == "success" else
               MODERN_COLORS['warning'] if notification_type == "warning" else
               MODERN_COLORS['danger'],
            height=30
        )
        notification_frame.pack(fill=X, side=TOP)
        notification_frame.pack_propagate(False)
        
        # Notification content
        notification_label = tk.Label(
            notification_frame,
            text=f"📢 {message}",
            font=('Segoe UI', 10, 'bold'),
            bg=notification_frame.cget('bg'),
            fg='white'
        )
        notification_label.pack(expand=True)
        
        # Auto-hide notification
        self.after(duration, lambda: notification_frame.destroy())

    def start_status_updates(self):
        """Start periodic status updates"""
        def update_loop():
            self.update_time_display()
            
            # Simulate network check (you can replace with actual network check)
            try:
                # Simple network status simulation
                import socket
                socket.create_connection(("8.8.8.8", 53), timeout=3)
                if self.network_status != "connected":
                    self.update_network_status("connected", "Connected")
                    self.pulse_network_indicator()
            except:
                if self.network_status != "disconnected":
                    self.update_network_status("disconnected")
            
            # Schedule next update
            self.after(1000, update_loop)
        
        # Start the update loop
        update_loop()

    def set_station_status(self, status="active"):
        """Set station operational status"""
        status_configs = {
            "active": {
                "bg": MODERN_COLORS['success'],
                "text": "ACTIVE"
            },
            "idle": {
                "bg": MODERN_COLORS['warning'],
                "text": "IDLE"
            },
            "offline": {
                "bg": MODERN_COLORS['danger'],
                "text": "OFFLINE"
            },
            "maintenance": {
                "bg": MODERN_COLORS['secondary'],
                "text": "MAINTENANCE"
            }
        }
        
        # You can add a status indicator to the header if needed
        # This method provides the framework for status indication