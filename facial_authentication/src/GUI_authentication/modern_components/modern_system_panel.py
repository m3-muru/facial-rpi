import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk_modern
from ttkbootstrap.constants import *
from datetime import datetime, timedelta
import threading
import time
import psutil
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
    'info': '#06B6D4',
    'background': '#0F172A',
    'surface': '#1E293B',
    'surface_light': '#334155',
    'text_primary': '#F8FAFC',
    'text_secondary': '#CBD5E1',
    'accent': '#8B5CF6'
}

class ModernSystemPanel(ttk_modern.Frame):
    def __init__(self, parent, config):
        super().__init__(parent, style='Surface.TFrame')
        
        self.parent = parent
        self.config = config
        
        # System metrics
        self.start_time = datetime.now()
        self.daily_stats = {
            'successful_auths': 142,
            'failed_auths': 3,
            'total_attempts': 145,
            'avg_response_time': 1.2
        }
        
        # Component references
        self.system_status_items = {}
        self.performance_bars = {}  # Keep this for compatibility even if not used
        
        self.init_modern_ui()
        self.start_monitoring()

    def init_modern_ui(self):
        """Initialize modern system panel UI"""
        # Main container with padding
        main_container = ttk_modern.Frame(self, style='Surface.TFrame')
        main_container.pack(fill=BOTH, expand=True, padx=15, pady=15)
        
        # System Information Section
        self.init_system_info_section(main_container)
        
        # PERFORMANCE SECTION DISABLED
        # Uncomment the line below to re-enable performance metrics
        # self.init_performance_section(main_container)
        
        # Daily Statistics Section
        self.init_daily_stats_section(main_container)
        
        # Quick System Status Section
        # self.init_quick_status_section(main_container)

    def init_system_info_section(self, parent):
        """Initialize system information section"""
        # Header
        # info_header = self.create_section_header(parent, "💻 System Information")
        
        # Info container
        info_container = self.create_section_container(parent)
        
        # System info items
        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            
            system_info = [
                ("Station ID", self.config.PORT if hasattr(self.config, 'PORT') else "Unknown"),
                ("Hostname", hostname),
                ("IP Address", ip_address),
                ("Uptime", "Starting..."),
                ("Version", "ENVIS v2.0.0")
            ]
            
            for label, value in system_info:
                self.create_info_item(info_container, label, value, label.lower().replace(' ', '_'))
                
        except Exception as e:
            LOGGER.error(f"Failed to get system info: {e}")

    def init_performance_section(self, parent):
        """Initialize performance metrics section - DISABLED"""
        # This method is kept for compatibility but won't be called
        # You can remove this entire method if you want
        LOGGER.info("Performance section is disabled")
        pass

    def init_daily_stats_section(self, parent):
        """Initialize daily statistics section"""
        # Header
        # stats_header = self.create_section_header(parent, " Today's Activity")
        
        # Stats container
        stats_container = self.create_section_container(parent)
        
        # Stats grid - 2x2 layout
        stats_grid = tk.Frame(stats_container, bg=MODERN_COLORS['surface'])
        stats_grid.pack(fill=X, padx=10, pady=5)
        
        # Configure grid
        stats_grid.grid_columnconfigure(0, weight=1)
        stats_grid.grid_columnconfigure(1, weight=1)
        
        # Stat items
        # self.create_stat_card(stats_grid, "✅", "142", "Successful", 0, 0, MODERN_COLORS['success'])
        # self.create_stat_card(stats_grid, "", "3", "Failed", 0, 1, MODERN_COLORS['danger'])
        # self.create_stat_card(stats_grid, "", "98.2%", "Success Rate", 1, 0, MODERN_COLORS['info'])
        # self.create_stat_card(stats_grid, "⚡", "1.2s", "Avg Time", 1, 1, MODERN_COLORS['accent'])

    def init_quick_status_section(self, parent):
        """Initialize quick status indicators section"""
        # Header
        status_header = self.create_section_header(parent, "🔄 System Status")
        
        # Status container
        status_container = self.create_section_container(parent)
        
        # Status items
        status_items = [
            ("Database", "database", "connected"),
            ("Camera", "camera", "active"),
            ("Face Engine", "face_engine", "ready"),
            ("Network", "network", "online")
        ]
        
        for label, key, initial_status in status_items:
            self.create_status_indicator(status_container, label, key, initial_status)

    def create_section_header(self, parent, title):
        """Create a section header"""
        header_frame = ttk_modern.Frame(parent, style='Surface.TFrame')
        header_frame.pack(fill=X, pady=(20, 10))
        
        header_label = ttk_modern.Label(
            header_frame,
            text=title,
            font=('Segoe UI', 11, 'bold'),
            foreground=MODERN_COLORS['text_primary'],
            background=MODERN_COLORS['surface_light']
        )
        header_label.pack(side=LEFT)
        
        return header_frame

    def create_section_container(self, parent):
        """Create a styled section container"""
        container = tk.Frame(
            parent,
            bg=MODERN_COLORS['surface'],
            relief='flat',
            bd=0,
            highlightbackground=MODERN_COLORS['surface_light'],
            highlightthickness=1
        )
        container.pack(fill=X, pady=(0, 10))
        
        return container

    def create_info_item(self, parent, label, value, key):
        """Create an information item"""
        item_frame = tk.Frame(parent, bg=MODERN_COLORS['surface'])
        item_frame.pack(fill=X, padx=10, pady=3)
        
        # Label
        label_widget = tk.Label(
            item_frame,
            text=f"{label}:",
            font=('Segoe UI', 9),
            bg=MODERN_COLORS['surface'],
            fg=MODERN_COLORS['text_secondary'],
            anchor='w'
        )
        label_widget.pack(side=LEFT)
        
        # Value
        value_widget = tk.Label(
            item_frame,
            text=str(value),
            font=('Segoe UI', 9, 'bold'),
            bg=MODERN_COLORS['surface'],
            fg=MODERN_COLORS['text_primary'],
            anchor='e'
        )
        value_widget.pack(side=RIGHT)
        
        # Store reference for updates
        self.system_status_items[key] = value_widget

    def create_performance_metric(self, parent, label, key, unit):
        """Create a performance metric with progress bar - DISABLED"""
        # This method is kept for compatibility but won't be used
        LOGGER.debug(f"Performance metric creation disabled for: {label}")
        pass

    def create_stat_card(self, parent, icon, value, label, row, column, color):
        """Create a statistics card"""
        card_frame = tk.Frame(
            parent,
            bg=MODERN_COLORS['surface_light'],
            relief='flat',
            bd=0,
            highlightbackground=color,
            highlightthickness=2
        )
        card_frame.grid(row=row, column=column, padx=5, pady=5, sticky='ew')
        
        # Card content
        content_frame = tk.Frame(card_frame, bg=MODERN_COLORS['surface_light'])
        content_frame.pack(fill=BOTH, expand=True, padx=8, pady=8)
        
        # Icon
        icon_label = tk.Label(
            content_frame,
            text=icon,
            font=('Segoe UI', 16),
            bg=MODERN_COLORS['surface_light'],
            fg=color
        )
        icon_label.pack()
        
        # Value
        value_label = tk.Label(
            content_frame,
            text=value,
            font=('Segoe UI', 14, 'bold'),
            bg=MODERN_COLORS['surface_light'],
            fg=MODERN_COLORS['text_primary']
        )
        value_label.pack()
        
        # Label
        label_widget = tk.Label(
            content_frame,
            text=label,
            font=('Segoe UI', 8),
            bg=MODERN_COLORS['surface_light'],
            fg=MODERN_COLORS['text_secondary']
        )
        label_widget.pack()

    def create_status_indicator(self, parent, label, key, status):
        """Create a status indicator"""
        status_frame = tk.Frame(parent, bg=MODERN_COLORS['surface'])
        status_frame.pack(fill=X, padx=10, pady=3)
        
        # Status dot
        status_dot = tk.Label(
            status_frame,
            text="●",
            font=('Segoe UI', 12),
            bg=MODERN_COLORS['surface'],
            fg=self.get_status_color(status)
        )
        status_dot.pack(side=LEFT, padx=(0, 8))
        
        # Label
        label_widget = tk.Label(
            status_frame,
            text=label,
            font=('Segoe UI', 9),
            bg=MODERN_COLORS['surface'],
            fg=MODERN_COLORS['text_secondary'],
            anchor='w'
        )
        label_widget.pack(side=LEFT, fill=X, expand=True)
        
        # Status text
        status_widget = tk.Label(
            status_frame,
            text=status.title(),
            font=('Segoe UI', 9, 'bold'),
            bg=MODERN_COLORS['surface'],
            fg=self.get_status_color(status),
            anchor='e'
        )
        status_widget.pack(side=RIGHT)
        
        # Store references
        self.system_status_items[key] = {
            'dot': status_dot,
            'status': status_widget
        }

    def get_status_color(self, status):
        """Get color for status"""
        status_colors = {
            'connected': MODERN_COLORS['success'],
            'active': MODERN_COLORS['success'],
            'ready': MODERN_COLORS['success'],
            'online': MODERN_COLORS['success'],
            'disconnected': MODERN_COLORS['danger'],
            'inactive': MODERN_COLORS['danger'],
            'offline': MODERN_COLORS['danger'],
            'error': MODERN_COLORS['danger'],
            'warning': MODERN_COLORS['warning'],
            'loading': MODERN_COLORS['info']
        }
        return status_colors.get(status.lower(), MODERN_COLORS['text_secondary'])

    def update_system_info(self):
        """Update system information"""
        try:
            # Update uptime
            uptime = datetime.now() - self.start_time
            uptime_str = str(uptime).split('.')[0]  # Remove microseconds
            
            if 'uptime' in self.system_status_items:
                self.system_status_items['uptime'].configure(text=uptime_str)
                
        except Exception as e:
            LOGGER.debug(f"Error updating system info: {e}")

    def update_performance_metrics(self):
        """Update performance metrics - DISABLED"""
        # Performance monitoring is disabled
        LOGGER.debug("Performance metrics update is disabled")
        pass

    def update_status_indicator(self, key, status):
        """Update a specific status indicator"""
        if key in self.system_status_items and isinstance(self.system_status_items[key], dict):
            color = self.get_status_color(status)
            self.system_status_items[key]['dot'].configure(fg=color)
            self.system_status_items[key]['status'].configure(
                text=status.title(),
                fg=color
            )

    def update_daily_stats(self, successful_auths=None, failed_auths=None):
        """Update daily statistics"""
        if successful_auths is not None:
            self.daily_stats['successful_auths'] = successful_auths
        if failed_auths is not None:
            self.daily_stats['failed_auths'] = failed_auths
            
        # Recalculate derived stats
        total = self.daily_stats['successful_auths'] + self.daily_stats['failed_auths']
        self.daily_stats['total_attempts'] = total
        
        if total > 0:
            success_rate = (self.daily_stats['successful_auths'] / total) * 100
        else:
            success_rate = 0
            
        # Update display (you would need to store references to update the cards)

    def start_monitoring(self):
        """Start system monitoring - Performance monitoring disabled"""
        def monitoring_loop():
            while True:
                try:
                    # Schedule UI updates on main thread
                    self.after_idle(self.update_system_info)
                    # Performance metrics update is disabled
                    # self.after_idle(self.update_performance_metrics)
                    
                    # Update status indicators based on actual system state
                    
                    time.sleep(2)  # Update every 2 seconds
                except Exception as e:
                    LOGGER.error(f"Error in monitoring loop: {e}")
                    time.sleep(5)  # Wait longer on error
        
        # Start monitoring in background thread
        monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitoring_thread.start()

    # All other methods remain the same...
    def show_authentication_event(self, employee_id, success=True):
        """Show authentication event notification"""
        if success:
            self.daily_stats['successful_auths'] += 1
        else:
            self.daily_stats['failed_auths'] += 1
            
        self.update_daily_stats()

    def set_database_status(self, status):
        """Set database connection status"""
        self.update_status_indicator('database', status)

    def set_camera_status(self, status):
        """Set camera status"""
        self.update_status_indicator('camera', status)

    def set_face_engine_status(self, status):
        """Set face recognition engine status"""
        self.update_status_indicator('face_engine', status)

    def set_network_status(self, status):
        """Set network connection status"""
        self.update_status_indicator('network', status)

    def add_notification(self, message, notification_type="info"):
        """Add a notification to the system panel"""
        notification_frame = tk.Frame(
            self,
            bg=MODERN_COLORS.get(notification_type, MODERN_COLORS['info']),
            height=30
        )
        notification_frame.pack(fill=X, side=TOP, before=self.children[list(self.children.keys())[0]])
        notification_frame.pack_propagate(False)
        
        notification_label = tk.Label(
            notification_frame,
            text=f"🔔 {message}",
            font=('Segoe UI', 9, 'bold'),
            bg=notification_frame.cget('bg'),
            fg='white'
        )
        notification_label.pack(expand=True)
        
        self.after(3000, lambda: notification_frame.destroy())

    def get_system_summary(self):
        """Get system summary for external monitoring - Performance data excluded"""
        try:
            uptime = datetime.now() - self.start_time
            
            return {
                'uptime_seconds': int(uptime.total_seconds()),
                'daily_stats': self.daily_stats.copy(),
                'timestamp': datetime.now().isoformat()
                # Performance metrics removed: 'cpu_usage', 'memory_usage'
            }
        except Exception as e:
            LOGGER.error(f"Error getting system summary: {e}")
            return {}