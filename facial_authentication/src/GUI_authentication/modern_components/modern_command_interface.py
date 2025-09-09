import queue
import threading
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk_modern
from ttkbootstrap.constants import *
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

class ModernCommandInterface(ttk_modern.Frame):
    def __init__(self, parent, config, cmd_request_q, ready_status_q):
        super().__init__(parent, style='Surface.TFrame')
        
        self.parent = parent
        self.config = config
        self.cmd_request_q = cmd_request_q
        self.ready_status_q = ready_status_q
        
        # Button states
        self.buttons_enabled = True
        self.current_operation = None
        
        self.init_modern_ui()
        self.setup_keybindings()
        self.spawn_ready_status_poller_thread()
        
        # Auto-start authentication
        self.put_command_request('authenticate')

    def init_modern_ui(self):
        """Initialize modern command interface UI"""
        # Main container with padding
        main_container = ttk_modern.Frame(self, style='Surface.TFrame')
        main_container.pack(fill=BOTH, expand=True, padx=15, pady=10)
        
        # Header
        header_frame = ttk_modern.Frame(main_container, style='Surface.TFrame')
        header_frame.pack(fill=X, pady=(0, 15))
        
        title_label = ttk_modern.Label(
            header_frame,
            text="🎮 Quick Actions",
            font=('Segoe UI', 12, 'bold'),
            foreground=MODERN_COLORS['text_primary'],
            background=MODERN_COLORS['surface_light']
        )
        title_label.pack(side=LEFT)
        
        # Status indicator for ready state
        self.ready_indicator = ttk_modern.Label(
            header_frame,
            text="⚪ Initializing",
            font=('Segoe UI', 9),
            foreground=MODERN_COLORS['text_secondary'],
            background=MODERN_COLORS['surface_light']
        )
        self.ready_indicator.pack(side=RIGHT)
        
        # Button container
        button_container = ttk_modern.Frame(main_container, style='Surface.TFrame')
        button_container.pack(fill=X)
        
        # Configure grid
        button_container.grid_columnconfigure(0, weight=1)
        button_container.grid_columnconfigure(1, weight=1)
        button_container.grid_columnconfigure(2, weight=1)
        
        # Primary action button - Start Authentication
        self.btn_authenticate = self.create_modern_button(
            button_container,
            text=" Start Scan",
            command=lambda: self.put_command_request('authenticate'),
            style_type="primary",
            row=0, column=0,
            tooltip="Start face authentication process"
        )
        
        # Secondary action button - Resync
        self.btn_resync = self.create_modern_button(
            button_container,
            text="🔄 Resync",
            command=lambda: self.put_command_request('resync'),
            style_type="secondary",
            row=0, column=1,
            tooltip="Resync face database"
        )
        
        # Settings/Emergency button
        self.btn_settings = self.create_modern_button(
            button_container,
            text="⚙️ Settings",
            command=self.show_settings_menu,
            style_type="outline",
            row=0, column=2,
            tooltip="System settings and options"
        )
        
        # Status info panel
        self.init_status_info(main_container)
        
        # Keyboard shortcuts info
        self.init_shortcuts_info(main_container)

    def create_modern_button(self, parent, text, command, style_type="primary", 
                           row=0, column=0, tooltip=None):
        """Create a modern styled button"""
        
        # Button style configurations
        style_configs = {
            "primary": {
                "style": "primary.TButton",
                "bg": MODERN_COLORS['primary'],
                "fg": "white"
            },
            "secondary": {
                "style": "secondary.TButton", 
                "bg": MODERN_COLORS['secondary'],
                "fg": "white"
            },
            "success": {
                "style": "success.TButton",
                "bg": MODERN_COLORS['success'],
                "fg": "white"
            },
            "warning": {
                "style": "warning.TButton",
                "bg": MODERN_COLORS['warning'],
                "fg": "white"
            },
            "danger": {
                "style": "danger.TButton",
                "bg": MODERN_COLORS['danger'],
                "fg": "white"
            },
            "outline": {
                "style": "outline.TButton",
                "bg": MODERN_COLORS['surface_light'],
                "fg": MODERN_COLORS['text_primary']
            }
        }
        
        config = style_configs.get(style_type, style_configs["primary"])
        
        # Create button with modern styling
        btn = ttk_modern.Button(
            parent,
            text=text,
            command=command,
            style=config["style"],
            width=12
        )
        
        btn.grid(row=row, column=column, padx=5, pady=5, sticky="ew")
        
        # Add tooltip if provided
        if tooltip:
            self.add_tooltip(btn, tooltip)
            
        return btn

    def add_tooltip(self, widget, text):
        """Add tooltip to widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(
                tooltip,
                text=text,
                background=MODERN_COLORS['surface'],
                foreground=MODERN_COLORS['text_primary'],
                relief="solid",
                borderwidth=1,
                font=('Segoe UI', 8),
                padx=5,
                pady=3
            )
            label.pack()
            
            widget.tooltip = tooltip
            
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
                
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def init_status_info(self, parent):
        """Initialize status information panel"""
        status_frame = ttk_modern.Frame(parent, style='Surface.TFrame')
        status_frame.pack(fill=X, pady=(10, 0))
        
        # Current operation display
        self.operation_frame = tk.Frame(
            status_frame,
            bg=MODERN_COLORS['surface'],
            relief='flat',
            bd=0,
            highlightbackground=MODERN_COLORS['surface_light'],
            highlightthickness=1
        )
        self.operation_frame.pack(fill=X, padx=0, pady=5)
        
        operation_content = tk.Frame(
            self.operation_frame,
            bg=MODERN_COLORS['surface'],
            padx=10,
            pady=8
        )
        operation_content.pack(fill=X)
        
        # Operation status
        self.operation_label = tk.Label(
            operation_content,
            text="🔄 System Ready - Press 'Start Scan' to begin",
            font=('Segoe UI', 10),
            bg=MODERN_COLORS['surface'],
            fg=MODERN_COLORS['text_secondary'],
            anchor='w'
        )
        self.operation_label.pack(fill=X)

    def init_shortcuts_info(self, parent):
        """Initialize keyboard shortcuts information"""
        shortcuts_frame = ttk_modern.Frame(parent, style='Surface.TFrame')
        shortcuts_frame.pack(fill=X, pady=(5, 0))
        
        shortcuts_label = ttk_modern.Label(
            shortcuts_frame,
            text="⌨️ Shortcuts: ESC=Exit | F1=Center | F2=Top Right",
            font=('Segoe UI', 8),
            foreground=MODERN_COLORS['text_secondary'],
            background=MODERN_COLORS['surface_light']
        )
        shortcuts_label.pack(anchor='w')

    def setup_keybindings(self):
        """Setup keyboard bindings"""
        # Get the root window
        root = self.winfo_toplevel()
        
        # Bind keys to root window
        root.bind('<Return>', lambda event: self.put_command_request('authenticate'))
        root.bind('<Escape>', lambda event: self.parent.quit_app())
        root.bind('<F5>', lambda event: self.put_command_request('resync'))

    def show_settings_menu(self):
        """Show settings/options menu"""
        # Create popup menu
        menu = tk.Menu(self, tearoff=0)
        menu.configure(
            bg=MODERN_COLORS['surface'],
            fg=MODERN_COLORS['text_primary'],
            activebackground=MODERN_COLORS['primary'],
            activeforeground='white',
            relief='flat',
            bd=1
        )
        
        menu.add_command(label="🔄 Resync Database", 
                        command=lambda: self.put_command_request('resync'))
        menu.add_separator()
        menu.add_command(label="👤 Enroll New User", 
                        command=self.show_enroll_dialog)
        menu.add_separator()
        menu.add_command(label="🗑️ Remove All Users", 
                        command=lambda: self.put_command_request('d'))
        menu.add_separator()
        menu.add_command(label=" Exit Application", 
                        command=lambda: self.put_command_request('quit'))
        
        # Show menu at button location
        try:
            x = self.btn_settings.winfo_rootx()
            y = self.btn_settings.winfo_rooty() + self.btn_settings.winfo_height()
            menu.post(x, y)
        except:
            menu.post(self.winfo_pointerx(), self.winfo_pointery())

    def show_enroll_dialog(self):
        """Show enrollment dialog"""
        from src.GUI_authentication.enroll_popup_window import EnrollPopupWindow
        
        dialog = EnrollPopupWindow(self)
        self.wait_window(dialog)
        
        # Get employee ID and start enrollment
        employee_id = dialog.get_input()
        if employee_id:
            self.put_command_request_with_data('enrol', {'employee_id': employee_id})

    def put_command_request(self, command):
        """Put command request in queue"""
        self.set_operation_status(f"🔄 Executing: {command.title()}")
        
        # Disable buttons temporarily to prevent spam
        self.ignore_all_bindings()
        
        request_dict = {"command": command}
        self.cmd_request_q.put(request_dict)
        
        # Re-enable after delay
        self.parent.after(3000, lambda: self.reinstate_all_bindings())

    def put_command_request_with_data(self, command, data):
        """Put command request with additional data"""
        self.set_operation_status(f"🔄 Executing: {command.title()}")
        
        request_dict = {"command": command}
        request_dict.update(data)
        self.cmd_request_q.put(request_dict)

    def set_operation_status(self, message):
        """Set current operation status"""
        self.operation_label.configure(text=message)
        self.current_operation = message

    def update_ready_status(self, is_ready):
        """Update ready status indicator"""
        if is_ready:
            self.ready_indicator.configure(
                text="🟢 Ready",
                foreground=MODERN_COLORS['success']
            )
            self.enable_buttons()
            self.set_operation_status(" System Ready - Press 'Start Scan' to begin")
        else:
            self.ready_indicator.configure(
                text="🟡 Busy",
                foreground=MODERN_COLORS['warning']
            )
            self.disable_buttons()

    def disable_buttons(self):
        """Disable all buttons"""
        self.buttons_enabled = False
        buttons = [self.btn_authenticate, self.btn_resync, self.btn_settings]
        
        for btn in buttons:
            btn.configure(state="disabled")

    def enable_buttons(self):
        """Enable all buttons"""
        self.buttons_enabled = True
        buttons = [self.btn_authenticate, self.btn_resync, self.btn_settings]
        
        for btn in buttons:
            btn.configure(state="normal")

    def focus_on_primary_btn(self):
        """Focus on primary button"""
        if self.buttons_enabled:
            self.btn_authenticate.focus()

    def init_ready_status_q_poller(self):
        """Initialize ready status queue poller"""
        def _retrieve_ready_status():
            while True:
                try:
                    is_ready = self.ready_status_q.get()
                    # Schedule UI update on main thread
                    self.after_idle(lambda ready=is_ready: self.update_ready_status(ready))
                except Exception as e:
                    LOGGER.error(f"Error processing ready status: {e}")

        # Run in background thread
        thread = threading.Thread(target=_retrieve_ready_status, daemon=True)
        thread.start()

    def spawn_ready_status_poller_thread(self):
        """Start ready status polling thread"""
        self.init_ready_status_q_poller()

    def ignore_all_bindings(self):
        """Temporarily ignore all key bindings"""
        def _ignore_all_bindings(event):
            LOGGER.debug(f'Keyboard event binding ignored: {event}')
            return "break"
            
        root = self.winfo_toplevel()
        root.bind('<Return>', _ignore_all_bindings)
        root.bind('<Escape>', _ignore_all_bindings)

    def reinstate_all_bindings(self):
        """Reinstate all key bindings"""
        root = self.winfo_toplevel()
        root.bind('<Return>', lambda event: self.put_command_request('authenticate'))
        root.bind('<Escape>', lambda event: self.parent.quit_app())

    def show_processing_state(self, message="Processing..."):
        """Show processing state with animation"""
        self.set_operation_status(f"⏳ {message}")
        
        # Add pulsing animation to the operation label
        self.animate_processing()

    def animate_processing(self):
        """Animate processing indicator"""
        if "⏳" in self.operation_label.cget("text"):
            # Simple text animation
            current_text = self.operation_label.cget("text")
            if current_text.endswith("..."):
                new_text = current_text[:-3] + "."
            elif current_text.endswith(".."):
                new_text = current_text + "."
            elif current_text.endswith("."):
                new_text = current_text + "."
            else:
                new_text = current_text + "."
                
            self.operation_label.configure(text=new_text)
            self.after(500, self.animate_processing)

    def show_success_state(self, message="Operation completed successfully"):
        """Show success state"""
        self.set_operation_status(f" {message}")

    def show_error_state(self, message="Operation failed"):
        """Show error state"""
        self.set_operation_status(f" {message}")

    def show_warning_state(self, message="Warning"):
        """Show warning state"""
        self.set_operation_status(f"⚠️ {message}")