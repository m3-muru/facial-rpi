import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk_modern
from ttkbootstrap.constants import *
import threading
import queue
from datetime import datetime
import src.utility.gui_feedback_color_utility as color_utility
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

class ModernStatusBar(ttk_modern.Frame):
    def __init__(self, parent, feedback_msg_q):
        super().__init__(parent, style='Surface.TFrame')
        
        self.parent = parent
        self.feedback_msg_q = feedback_msg_q
        
        # Animation properties
        self.pulse_alpha = 0
        self.pulse_direction = 1
        self.is_animating = False
        
        # Progress tracking
        self.progress_value = 0
        self.target_progress = 0
        
        self.init_modern_ui()
        self.spawn_feedback_poller_thread()

    def init_modern_ui(self):
        """Initialize modern status bar UI"""
        # Main container with padding
        main_container = ttk_modern.Frame(self, style='Surface.TFrame')
        main_container.pack(fill=BOTH, expand=True, padx=15, pady=15)
        
        # Header
        header_frame = ttk_modern.Frame(main_container, style='Surface.TFrame')
        header_frame.pack(fill=X, pady=(0, 10))
        
        title_label = ttk_modern.Label(
            header_frame,
            text="👁️ Authentication Status",
            font=('Segoe UI', 12, 'bold'),
            foreground=MODERN_COLORS['text_primary'],
            background=MODERN_COLORS['surface_light']
        )
        title_label.pack(side=LEFT)
        
        # Timestamp
        self.timestamp_label = ttk_modern.Label(
            header_frame,
            text="",
            font=('Segoe UI', 8),
            foreground=MODERN_COLORS['text_secondary'],
            background=MODERN_COLORS['surface_light']
        )
        self.timestamp_label.pack(side=RIGHT)
        
        # Status container with modern styling
        self.status_container = tk.Frame(
            main_container,
            bg=MODERN_COLORS['surface'],
            relief='flat',
            bd=0,
            highlightbackground=MODERN_COLORS['surface_light'],
            highlightthickness=1
        )
        self.status_container.pack(fill=X, pady=(0, 10))
        
        # Status content frame
        status_content = tk.Frame(
            self.status_container,
            bg=MODERN_COLORS['surface'],
            padx=15,
            pady=15
        )
        status_content.pack(fill=BOTH, expand=True)
        
        # Status icon and text frame
        status_main_frame = tk.Frame(status_content, bg=MODERN_COLORS['surface'])
        status_main_frame.pack(fill=X)
        
        # Status icon
        self.status_icon = tk.Label(
            status_main_frame,
            text="⚪",
            font=('Segoe UI', 16),
            bg=MODERN_COLORS['surface'],
            fg=MODERN_COLORS['text_secondary']
        )
        self.status_icon.pack(side=LEFT, padx=(0, 10))
        
        # Status text
        self.status_text = tk.Label(
            status_main_frame,
            text="System Ready",
            font=('Segoe UI', 11, 'bold'),
            bg=MODERN_COLORS['surface'],
            fg=MODERN_COLORS['text_primary'],
            wraplength=200,
            justify=LEFT
        )
        self.status_text.pack(side=LEFT, fill=X, expand=True)
        
        # Progress bar frame
        self.progress_frame = tk.Frame(status_content, bg=MODERN_COLORS['surface'])
        self.progress_frame.pack(fill=X, pady=(10, 0))
        
        # Progress bar (initially hidden)
        self.progress_bar = ttk_modern.Progressbar(
            self.progress_frame,
            mode='determinate',
            length=200,
            style='success.Horizontal.TProgressbar'
        )
        
        # Recent activity section
        self.init_recent_activity(main_container)

    def init_recent_activity(self, parent):
        """Initialize recent activity section"""
        activity_frame = ttk_modern.Frame(parent, style='Surface.TFrame')
        activity_frame.pack(fill=X)
        
        # Activity header
        activity_header = ttk_modern.Label(
            activity_frame,
            text=" Recent Activity",
            font=('Segoe UI', 10, 'bold'),
            foreground=MODERN_COLORS['text_primary'],
            background=MODERN_COLORS['surface_light']
        )
        activity_header.pack(anchor=W, pady=(0, 5))
        
        # Activity list frame
        self.activity_container = tk.Frame(
            activity_frame,
            bg=MODERN_COLORS['surface'],
            relief='flat',
            bd=0,
            highlightbackground=MODERN_COLORS['surface_light'],
            highlightthickness=1
        )
        self.activity_container.pack(fill=X)
        
        # Activity items (initially empty)
        self.activity_items = []
        self.max_activity_items = 3
        
        # Initialize with placeholder
        self.add_activity_item("System initialized", "info")

    def add_activity_item(self, message, status_type="info"):
        """Add an activity item to the recent activity list"""
        # Remove oldest item if we have too many
        if len(self.activity_items) >= self.max_activity_items:
            self.activity_items[0].destroy()
            self.activity_items.pop(0)
        
        # Create new activity item
        item_frame = tk.Frame(
            self.activity_container,
            bg=MODERN_COLORS['surface'],
            padx=10,
            pady=5
        )
        item_frame.pack(fill=X, padx=5, pady=2)
        
        # Status indicator
        status_colors = {
            'success': '🟢',
            'danger': '🔴',
            'warning': '🟡',
            'info': '🔵',
            'processing': '🟡'
        }
        
        indicator = tk.Label(
            item_frame,
            text=status_colors.get(status_type, '⚪'),
            font=('Segoe UI', 10),
            bg=MODERN_COLORS['surface']
        )
        indicator.pack(side=LEFT, padx=(0, 8))
        
        # Message
        msg_label = tk.Label(
            item_frame,
            text=message,
            font=('Segoe UI', 9),
            bg=MODERN_COLORS['surface'],
            fg=MODERN_COLORS['text_secondary'],
            wraplength=180,
            justify=LEFT
        )
        msg_label.pack(side=LEFT, fill=X, expand=True)
        
        # Timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        time_label = tk.Label(
            item_frame,
            text=timestamp,
            font=('Segoe UI', 8),
            bg=MODERN_COLORS['surface'],
            fg=MODERN_COLORS['text_secondary']
        )
        time_label.pack(side=RIGHT)
        
        # Store reference
        self.activity_items.append(item_frame)

    def get_status_config(self, status_type):
        """Get configuration for status type"""
        configs = {
            'success': {
                'icon': '',
                'color': MODERN_COLORS['success'],
                'bg_color': MODERN_COLORS['surface']
            },
            'danger': {
                'icon': '',
                'color': MODERN_COLORS['danger'],
                'bg_color': MODERN_COLORS['surface']
            },
            'warning': {
                'icon': '⚠️',
                'color': MODERN_COLORS['warning'],
                'bg_color': MODERN_COLORS['surface']
            },
            'info': {
                'icon': 'ℹ️',
                'color': MODERN_COLORS['info'],
                'bg_color': MODERN_COLORS['surface']
            },
            'processing': {
                'icon': '⏳',
                'color': MODERN_COLORS['primary'],
                'bg_color': MODERN_COLORS['surface']
            }
        }
        return configs.get(status_type, configs['info'])

    def set_msg(self, msg, status_type='info'):
        """Set status message with type"""
        config = self.get_status_config(status_type)
        
        # Update icon and text
        self.status_icon.configure(
            text=config['icon'],
            fg=config['color']
        )
        
        self.status_text.configure(
            text=msg,
            fg=MODERN_COLORS['text_primary']
        )
        
        # Update container border color
        self.status_container.configure(
            highlightbackground=config['color']
        )
        
        # Update timestamp
        self.timestamp_label.configure(
            text=datetime.now().strftime("%H:%M:%S")
        )
        
        # Add to recent activity
        self.add_activity_item(msg, status_type)
        
        # Start animation for important statuses
        if status_type in ['processing', 'warning', 'danger']:
            self.start_pulse_animation()
        else:
            self.stop_pulse_animation()
        
        # Auto-hide progress bar for non-processing statuses
        if status_type != 'processing':
            self.hide_progress()

    def set_msg_with_progress(self, msg, progress=0, status_type='processing'):
        """Set message with progress bar"""
        self.set_msg(msg, status_type)
        self.show_progress(progress)

    def show_progress(self, value=0):
        """Show and update progress bar"""
        self.progress_bar.pack(fill=X, pady=(5, 0))
        self.target_progress = value
        self.animate_progress()

    def hide_progress(self):
        """Hide progress bar"""
        self.progress_bar.pack_forget()
        self.progress_value = 0
        self.target_progress = 0

    def animate_progress(self):
        """Animate progress bar to target value"""
        if abs(self.progress_value - self.target_progress) < 1:
            self.progress_value = self.target_progress
            self.progress_bar['value'] = self.progress_value
            return
        
        # Smooth animation
        diff = self.target_progress - self.progress_value
        self.progress_value += diff * 0.1
        self.progress_bar['value'] = self.progress_value
        
        # Continue animation
        self.after(50, self.animate_progress)

    def start_pulse_animation(self):
        """Start pulse animation for status icon"""
        self.is_animating = True
        self.pulse_animation()

    def stop_pulse_animation(self):
        """Stop pulse animation"""
        self.is_animating = False

    def pulse_animation(self):
        """Pulse animation for status icon"""
        if not self.is_animating:
            return
            
        try:
            # Simple alpha pulse effect by changing font size slightly
            base_size = 16
            pulse_size = int(base_size + (self.pulse_alpha / 50))
            
            self.status_icon.configure(font=('Segoe UI', pulse_size))
            
            self.pulse_alpha += self.pulse_direction * 5
            if self.pulse_alpha >= 50:
                self.pulse_direction = -1
            elif self.pulse_alpha <= 0:
                self.pulse_direction = 1
            
            # Continue animation
            self.after(100, self.pulse_animation)
            
        except Exception as e:
            LOGGER.debug(f"Pulse animation error: {e}")

    def set_feedback(self, feedback):
        """Set feedback from queue (legacy compatibility)"""
        msg = feedback.get("msg", "Unknown status")
        status = feedback.get("status")
        
        # Map old status types to new ones
        status_mapping = {
            'PENDING': 'processing',
            'ACCEPTED': 'success',
            'REJECTED': 'danger'
        }
        
        if hasattr(status, 'name'):
            status_type = status_mapping.get(status.name, 'info')
        else:
            # Determine status type from message content
            if any(word in msg.lower() for word in ['success', 'successful', 'accepted']):
                status_type = 'success'
            elif any(word in msg.lower() for word in ['error', 'failed', 'failure', 'forbidden']):
                status_type = 'danger'
            elif any(word in msg.lower() for word in ['warning', 'wait']):
                status_type = 'warning'
            elif any(word in msg.lower() for word in ['processing', 'authenticating']):
                status_type = 'processing'
            else:
                status_type = 'info'
        
        self.set_msg(msg, status_type)

    def init_retrieve_feedback_q_poller(self):
        """Initialize feedback queue poller"""
        def _retrieve_feedback():
            while True:
                try:
                    feedback = self.feedback_msg_q.get()
                    # Schedule UI update on main thread
                    self.after_idle(lambda f=feedback: self.set_feedback(f))
                except Exception as e:
                    LOGGER.error(f"Error processing feedback: {e}")

        # Run in background thread
        thread = threading.Thread(target=_retrieve_feedback, daemon=True)
        thread.start()

    def spawn_feedback_poller_thread(self):
        """Start feedback polling thread"""
        self.init_retrieve_feedback_q_poller()

    def show_authentication_progress(self, employee_id=None):
        """Show authentication in progress"""
        msg = f"Authenticating {employee_id}..." if employee_id else "Authentication in progress..."
        self.set_msg_with_progress(msg, 0, 'processing')
        
        # Simulate progress
        self.simulate_auth_progress()

    def simulate_auth_progress(self):
        """Simulate authentication progress"""
        progress_steps = [20, 40, 60, 80, 100]
        
        def update_progress(step_index=0):
            if step_index < len(progress_steps):
                self.show_progress(progress_steps[step_index])
                self.after(200, lambda: update_progress(step_index + 1))
        
        update_progress()

    def show_success(self, employee_id):
        """Show authentication success"""
        self.set_msg(f" Welcome {employee_id}", 'success')
        self.hide_progress()

    def show_failure(self, reason="Authentication failed"):
        """Show authentication failure"""
        self.set_msg(f" {reason}", 'danger')
        self.hide_progress()