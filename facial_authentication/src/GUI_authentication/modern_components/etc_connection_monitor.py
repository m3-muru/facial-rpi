import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk_modern
from ttkbootstrap.constants import *
from datetime import datetime
import threading
import time
import src.logger.custom_logger as custom_logger

LOGGER = custom_logger.get_logger()

# Modern color scheme
MODERN_COLORS = {
    'primary': '#2563EB',
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

class ETCStatusWidget(ttk_modern.Frame):
    """
    Modern widget to display ETC connection status in the UI
    """
    
    def __init__(self, parent, etc_monitor=None, **kwargs):
        super().__init__(parent, style='Surface.TFrame', **kwargs)
        
        self.parent = parent
        self.etc_monitor = etc_monitor
        
        # Status tracking
        self.current_status = {
            'etc_web': False,
            'websocket': False,
            'overall': 'disconnected',
            'last_check': None
        }
        
        # Animation properties
        self.pulse_alpha = 0
        self.pulse_direction = 1
        self.is_animating = False
        
        self.init_ui()
        
        # Register with monitor if provided
        if self.etc_monitor:
            self.etc_monitor.add_status_callback(self.on_status_update)
    
    def init_ui(self):
        """Initialize the ETC status widget UI"""
        # Main container
        main_container = ttk_modern.Frame(self, style='Surface.TFrame')
        main_container.pack(fill=BOTH, expand=True, padx=15, pady=10)
        
        # Header with title and last check time
        header_frame = ttk_modern.Frame(main_container, style='Surface.TFrame')
        header_frame.pack(fill=X, pady=(0, 10))
        
        title_label = ttk_modern.Label(
            header_frame,
            text=" ETC Connection",
            font=('Segoe UI', 12, 'bold'),
            foreground=MODERN_COLORS['text_primary'],
            background=MODERN_COLORS['surface_light']
        )
        title_label.pack(side=LEFT)
        
        self.last_check_label = ttk_modern.Label(
            header_frame,
            text="Never checked",
            font=('Segoe UI', 8),
            foreground=MODERN_COLORS['text_secondary'],
            background=MODERN_COLORS['surface_light']
        )
        self.last_check_label.pack(side=RIGHT)
        
        # Overall status container
        self.status_container = tk.Frame(
            main_container,
            bg=MODERN_COLORS['surface'],
            relief='flat',
            bd=0,
            highlightbackground=MODERN_COLORS['surface_light'],
            highlightthickness=1
        )
        self.status_container.pack(fill=X, pady=(0, 10))
        
        # Overall status content
        status_content = tk.Frame(self.status_container, bg=MODERN_COLORS['surface'])
        status_content.pack(fill=BOTH, expand=True, padx=12, pady=10)
        
        # Status icon and text
        status_main = tk.Frame(status_content, bg=MODERN_COLORS['surface'])
        status_main.pack(fill=X)
        
        self.overall_icon = tk.Label(
            status_main,
            text="🔴",
            font=('Segoe UI', 16),
            bg=MODERN_COLORS['surface']
        )
        self.overall_icon.pack(side=LEFT, padx=(0, 10))
        
        self.overall_text = tk.Label(
            status_main,
            text="ETC Disconnected",
            font=('Segoe UI', 11, 'bold'),
            bg=MODERN_COLORS['surface'],
            fg=MODERN_COLORS['text_primary']
        )
        self.overall_text.pack(side=LEFT, fill=X, expand=True)
        
        # Test connection button
        self.test_button = ttk_modern.Button(
            status_main,
            text="🔄 Test",
            command=self.test_connection,
            style="info.TButton",
            width=8
        )
        self.test_button.pack(side=RIGHT)
        
        # Detailed status section
        details_frame = ttk_modern.Frame(main_container, style='Surface.TFrame')
        details_frame.pack(fill=X)
        
        details_header = ttk_modern.Label(
            details_frame,
            text=" Connection Details",
            font=('Segoe UI', 10, 'bold'),
            foreground=MODERN_COLORS['text_primary'],
            background=MODERN_COLORS['surface_light']
        )
        details_header.pack(anchor=W, pady=(0, 5))
        
        # Details container
        self.details_container = tk.Frame(
            details_frame,
            bg=MODERN_COLORS['surface'],
            relief='flat',
            bd=0,
            highlightbackground=MODERN_COLORS['surface_light'],
            highlightthickness=1
        )
        self.details_container.pack(fill=X)
        
        # Create detail items
        self.create_detail_item("Web Interface", "etc_web", "")
        self.create_detail_item("WebSocket", "websocket", "⚡")
        
        # Action buttons
        self.init_action_buttons(main_container)
    
    def create_detail_item(self, label, key, icon):
        """Create a detailed status item"""
        item_frame = tk.Frame(self.details_container, bg=MODERN_COLORS['surface'])
        item_frame.pack(fill=X, padx=10, pady=3)
        
        # Icon
        icon_label = tk.Label(
            item_frame,
            text=icon,
            font=('Segoe UI', 12),
            bg=MODERN_COLORS['surface']
        )
        icon_label.pack(side=LEFT, padx=(0, 8))
        
        # Label
        label_widget = tk.Label(
            item_frame,
            text=label,
            font=('Segoe UI', 9),
            bg=MODERN_COLORS['surface'],
            fg=MODERN_COLORS['text_secondary']
        )
        label_widget.pack(side=LEFT, fill=X, expand=True)
        
        # Status indicator
        status_dot = tk.Label(
            item_frame,
            text="●",
            font=('Segoe UI', 10),
            bg=MODERN_COLORS['surface'],
            fg=MODERN_COLORS['danger']
        )
        status_dot.pack(side=LEFT, padx=(5, 0))
        
        # Status text
        status_text = tk.Label(
            item_frame,
            text="Disconnected",
            font=('Segoe UI', 8, 'bold'),
            bg=MODERN_COLORS['surface'],
            fg=MODERN_COLORS['danger']
        )
        status_text.pack(side=LEFT, padx=(3, 0))
        
        # Store references
        setattr(self, f"{key}_dot", status_dot)
        setattr(self, f"{key}_text", status_text)
        setattr(self, f"{key}_icon", icon_label)
    
    def init_action_buttons(self, parent):
        """Initialize action buttons"""
        actions_frame = ttk_modern.Frame(parent, style='Surface.TFrame')
        actions_frame.pack(fill=X, pady=(10, 0))
        
        # Button container
        button_container = tk.Frame(actions_frame, bg=MODERN_COLORS['surface_light'])
        button_container.pack(fill=X)
        
        # Open ETC button
        self.open_etc_button = ttk_modern.Button(
            button_container,
            text=" Open ETC Page",
            command=self.open_etc_page,
            style="primary.TButton",
            width=15
        )
        self.open_etc_button.pack(side=LEFT, padx=5, pady=5)
        
        # Refresh button
        self.refresh_button = ttk_modern.Button(
            button_container,
            text="🔄 Refresh",
            command=self.refresh_status,
            style="secondary.TButton", 
            width=12
        )
        self.refresh_button.pack(side=LEFT, padx=5, pady=5)
    
    def on_status_update(self, status_type, is_connected, details=None):
        """Handle status updates from the monitor"""
        # Schedule UI update on main thread
        self.after_idle(lambda: self._update_status_ui(status_type, is_connected, details))
    
    def _update_status_ui(self, status_type, is_connected, details=None):
        """Update the UI based on status change"""
        try:
            # Update individual status
            self.current_status[status_type] = is_connected
            
            # Update detail item
            if hasattr(self, f"{status_type}_dot"):
                dot = getattr(self, f"{status_type}_dot")
                text = getattr(self, f"{status_type}_text")
                icon = getattr(self, f"{status_type}_icon")
                
                if is_connected:
                    dot.configure(fg=MODERN_COLORS['success'])
                    text.configure(text="Connected", fg=MODERN_COLORS['success'])
                    # Add subtle animation for connection
                    self.animate_icon(icon, "success")
                else:
                    dot.configure(fg=MODERN_COLORS['danger'])
                    text.configure(text="Disconnected", fg=MODERN_COLORS['danger'])
            
            # Update overall status
            self._update_overall_status()
            
            # Update last check time
            self.last_check_label.configure(
                text=f"Last: {datetime.now().strftime('%H:%M:%S')}"
            )
            
        except Exception as e:
            LOGGER.error(f"Error updating ETC status UI: {e}")
    
    def _update_overall_status(self):
        """Update the overall connection status display"""
        etc_connected = self.current_status.get('etc_web', False)
        ws_connected = self.current_status.get('websocket', False)
        
        if etc_connected and ws_connected:
            # Fully connected
            status = "fully_connected"
            icon = "🟢"
            text = "ETC Fully Connected"
            color = MODERN_COLORS['success']
            bg_color = MODERN_COLORS['success']
        elif etc_connected or ws_connected:
            # Partially connected
            status = "partially_connected" 
            icon = "🟡"
            text = "ETC Partially Connected"
            color = MODERN_COLORS['warning']
            bg_color = MODERN_COLORS['warning']
        else:
            # Disconnected
            status = "disconnected"
            icon = "🔴"
            text = "ETC Disconnected"
            color = MODERN_COLORS['danger']
            bg_color = MODERN_COLORS['danger']
        
        # Update overall display
        self.overall_icon.configure(text=icon)
        self.overall_text.configure(text=text, fg=MODERN_COLORS['text_primary'])
        self.status_container.configure(highlightbackground=bg_color)
        
        # Store current status
        self.current_status['overall'] = status
        
        # Start/stop animation based on status
        if status == "disconnected":
            self.start_pulse_animation()
        else:
            self.stop_pulse_animation()
    
    def animate_icon(self, icon_widget, animation_type="success"):
        """Animate an icon to show status change"""
        try:
            original_size = 12
            if animation_type == "success":
                # Briefly enlarge and return to normal
                for size in [14, 16, 14, 12]:
                    icon_widget.configure(font=('Segoe UI', size))
                    self.update_idletasks()
                    self.after(100)
        except:
            pass
    
    def start_pulse_animation(self):
        """Start pulse animation for disconnected status"""
        self.is_animating = True
        self.pulse_animation()
    
    def stop_pulse_animation(self):
        """Stop pulse animation"""
        self.is_animating = False
    
    def pulse_animation(self):
        """Pulse animation for the overall status"""
        if not self.is_animating:
            return
        
        try:
            # Pulse the overall icon
            base_size = 16
            pulse_size = int(base_size + (self.pulse_alpha / 25))
            
            self.overall_icon.configure(font=('Segoe UI', pulse_size))
            
            self.pulse_alpha += self.pulse_direction * 8
            if self.pulse_alpha >= 50:
                self.pulse_direction = -1
            elif self.pulse_alpha <= 0:
                self.pulse_direction = 1
            
            # Continue animation
            self.after(150, self.pulse_animation)
            
        except Exception as e:
            LOGGER.debug(f"Pulse animation error: {e}")
    
    def test_connection(self):
        """Test the ETC connection immediately"""
        if self.etc_monitor:
            # Disable button during test
            self.test_button.configure(state="disabled", text="Testing...")
            
            def run_test():
                try:
                    # Run test in background thread
                    self.etc_monitor.test_connection_now()
                    
                    # Re-enable button on main thread
                    self.after_idle(lambda: self.test_button.configure(
                        state="normal", text="🔄 Test"
                    ))
                except Exception as e:
                    LOGGER.error(f"Error during ETC connection test: {e}")
                    self.after_idle(lambda: self.test_button.configure(
                        state="normal", text="🔄 Test"
                    ))
            
            # Run test in background thread
            threading.Thread(target=run_test, daemon=True).start()
        else:
            LOGGER.warning("No ETC monitor available for testing")
    
    def refresh_status(self):
        """Refresh the current status display"""
        if self.etc_monitor:
            status = self.etc_monitor.get_connection_status()
            
            # Update UI with current status
            self._update_status_ui("etc_web", status.get("etc_web_reachable", False))
            self._update_status_ui("websocket", status.get("websocket_reachable", False))
            
            # Update last check time
            if status.get("last_check"):
                try:
                    check_time = datetime.fromisoformat(status["last_check"])
                    self.last_check_label.configure(
                        text=f"Last: {check_time.strftime('%H:%M:%S')}"
                    )
                except:
                    pass
    
    def open_etc_page(self):
        """Open the ETC page in browser"""
        if self.etc_monitor:
            import webbrowser
            try:
                etc_url = self.etc_monitor.etc_full_url
                webbrowser.open(etc_url)
                LOGGER.info(f"Opening ETC page: {etc_url}")
            except Exception as e:
                LOGGER.error(f"Error opening ETC page: {e}")
    
    def get_status_summary(self):
        """Get a summary of the current status"""
        return {
            "overall_status": self.current_status.get('overall', 'unknown'),
            "etc_web_connected": self.current_status.get('etc_web', False),
            "websocket_connected": self.current_status.get('websocket', False),
            "last_update": self.current_status.get('last_check')
        }
    
    def set_monitor(self, etc_monitor):
        """Set or update the ETC monitor"""
        # Remove callback from old monitor
        if self.etc_monitor:
            self.etc_monitor.remove_status_callback(self.on_status_update)
        
        # Set new monitor
        self.etc_monitor = etc_monitor
        
        # Add callback to new monitor
        if self.etc_monitor:
            self.etc_monitor.add_status_callback(self.on_status_update)
            # Refresh status immediately
            self.refresh_status()


class CompactETCStatusWidget(ttk_modern.Frame):
    """
    Compact version of ETC status widget for limited space (400px width app)
    """
    
    def __init__(self, parent, etc_monitor=None, **kwargs):
        super().__init__(parent, style='Surface.TFrame', **kwargs)
        
        self.parent = parent
        self.etc_monitor = etc_monitor
        self.current_status = "disconnected"
        
        self.init_compact_ui()
        
        if self.etc_monitor:
            self.etc_monitor.add_status_callback(self.on_status_update)
    
    def init_compact_ui(self):
        """Initialize compact UI for 400px width"""
        # Single row container
        container = tk.Frame(self, bg=MODERN_COLORS['surface_light'], height=35)
        container.pack(fill=X, padx=5, pady=3)
        container.pack_propagate(False)
        
        # Left side - Status indicator
        left_frame = tk.Frame(container, bg=MODERN_COLORS['surface_light'])
        left_frame.pack(side=LEFT, fill=Y, padx=(5, 0))
        
        self.status_dot = tk.Label(
            left_frame,
            text="●",
            font=('Segoe UI', 10),
            bg=MODERN_COLORS['surface_light'],
            fg=MODERN_COLORS['danger']
        )
        self.status_dot.pack(side=LEFT, pady=8)
        
        self.status_text = tk.Label(
            left_frame,
            text="ETC",
            font=('Segoe UI', 9, 'bold'),
            bg=MODERN_COLORS['surface_light'],
            fg=MODERN_COLORS['text_secondary']
        )
        self.status_text.pack(side=LEFT, padx=(3, 0), pady=8)
        
        # Right side - Quick actions
        right_frame = tk.Frame(container, bg=MODERN_COLORS['surface_light'])
        right_frame.pack(side=RIGHT, fill=Y)
        
        # Test button (compact)
        self.test_btn = tk.Button(
            right_frame,
            text="🔄",
            font=('Segoe UI', 8),
            bg=MODERN_COLORS['info'],
            fg='white',
            relief='flat',
            bd=0,
            width=3,
            command=self.test_connection
        )
        self.test_btn.pack(side=RIGHT, padx=2, pady=6)
        
        # Open button (compact)
        self.open_btn = tk.Button(
            right_frame,
            text="",
            font=('Segoe UI', 8),
            bg=MODERN_COLORS['primary'],
            fg='white',
            relief='flat',
            bd=0,
            width=3,
            command=self.open_etc_page
        )
        self.open_btn.pack(side=RIGHT, padx=2, pady=6)
    
    def on_status_update(self, status_type, is_connected, details=None):
        """Handle status updates"""
        self.after_idle(lambda: self._update_compact_status())
    
    def _update_compact_status(self):
        """Update compact status display"""
        if not self.etc_monitor:
            return
            
        status = self.etc_monitor.get_connection_status()
        overall = status.get('overall_status', 'disconnected')
        
        if overall == "fully_connected":
            self.status_dot.configure(fg=MODERN_COLORS['success'])
            self.status_text.configure(text="ETC ✓", fg=MODERN_COLORS['success'])
        elif overall == "partially_connected":
            self.status_dot.configure(fg=MODERN_COLORS['warning'])
            self.status_text.configure(text="ETC ~", fg=MODERN_COLORS['warning'])
        else:
            self.status_dot.configure(fg=MODERN_COLORS['danger'])
            self.status_text.configure(text="ETC ✗", fg=MODERN_COLORS['danger'])
    
    def test_connection(self):
        """Test connection (compact version)"""
        if self.etc_monitor:
            self.test_btn.configure(text="⏳")
            threading.Thread(target=self._run_test, daemon=True).start()
    
    def _run_test(self):
        """Run test in background"""
        try:
            if self.etc_monitor:
                self.etc_monitor.test_connection_now()
        finally:
            self.after_idle(lambda: self.test_btn.configure(text="🔄"))
    
    def open_etc_page(self):
        """Open ETC page"""
        if self.etc_monitor:
            import webbrowser
            try:
                webbrowser.open(self.etc_monitor.etc_full_url)
            except Exception as e:
                LOGGER.error(f"Error opening ETC page: {e}")


# Integration helper functions
def add_etc_status_to_system_panel(system_panel, etc_monitor):
    """
    Add ETC status indicators to the existing system panel
    """
    try:
        # Add ETC-specific status items to the system panel
        if hasattr(system_panel, 'create_status_indicator'):
            system_panel.create_status_indicator(
                system_panel.details_container if hasattr(system_panel, 'details_container') else system_panel,
                "ETC Web Interface", 
                "etc_web", 
                "disconnected"
            )
            
            system_panel.create_status_indicator(
                system_panel.details_container if hasattr(system_panel, 'details_container') else system_panel,
                "ETC WebSocket", 
                "etc_websocket", 
                "disconnected"
            )
        
        # Create callback to update system panel
        def update_system_panel(status_type, is_connected, details=None):
            try:
                status_key = "etc_web" if status_type == "etc_web" else "etc_websocket"
                status_value = "connected" if is_connected else "disconnected"
                
                if hasattr(system_panel, 'update_status_indicator'):
                    system_panel.update_status_indicator(status_key, status_value)
                    
            except Exception as e:
                LOGGER.error(f"Error updating system panel ETC status: {e}")
        
        # Register callback
        etc_monitor.add_status_callback(update_system_panel)
        
        LOGGER.info("ETC status indicators added to system panel")
        
    except Exception as e:
        LOGGER.error(f"Error adding ETC status to system panel: {e}")


def integrate_etc_status_with_modern_app(app):
    """
    Integrate ETC status monitoring with the modern authentication app
    """
    try:
        from .etc_connection_monitor import ETCConnectionMonitor, integrate_with_authentication_app
        
        # Create and integrate the monitor
        etc_monitor = integrate_with_authentication_app(app)
        
        # Add ETC status widget to the app
        # For 400px width app, use compact version
        if hasattr(app, 'create_section_container'):
            # Add to existing sections
            etc_section = app.create_section_container(
                app.scrollable_frame, 
                " ETC Connection Status"
            )
            
            # Use compact widget for 400px width
            etc_widget = CompactETCStatusWidget(etc_section, etc_monitor)
            etc_widget.pack(fill=X, pady=(0, 5))
            
            # Store reference
            app.etc_status_widget = etc_widget
        
        # Also integrate with system panel if available
        if hasattr(app, 'system_panel'):
            add_etc_status_to_system_panel(app.system_panel, etc_monitor)
        
        LOGGER.info("ETC status monitoring fully integrated with modern app")
        return etc_monitor
        
    except Exception as e:
        LOGGER.error(f"Error integrating ETC status with modern app: {e}")
        return None


# Example usage for testing
def main():
    """Test the ETC status widget"""
    import tkinter as tk
    from etc_connection_monitor import ETCConnectionMonitor
    
    # Create test window
    root = tk.Tk()
    root.title("ETC Status Widget Test")
    root.geometry("400x600")
    root.configure(bg=MODERN_COLORS['background'])
    
    # Create monitor
    etc_monitor = ETCConnectionMonitor()
    
    # Create widget
    status_widget = ETCStatusWidget(root, etc_monitor)
    status_widget.pack(fill=BOTH, expand=True, padx=10, pady=10)
    
    # Start monitoring
    etc_monitor.start_monitoring()
    
    # Test initial connection
    etc_monitor.test_connection_now()
    
    try:
        root.mainloop()
    finally:
        etc_monitor.stop_monitoring()


if __name__ == "__main__":
    main()