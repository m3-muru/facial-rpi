import threading
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk_modern
from ttkbootstrap.constants import *
import queue
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import src.logger.custom_logger as custom_logger

LOGGER = custom_logger.get_logger()

# Modern color scheme
MODERN_COLORS = {
    'primary': '#2563EB',
    'success': '#10B981',
    'warning': '#F59E0B',
    'danger': '#EF4444',
    'background': '#0F172A',
    'surface': '#1E293B',
    'surface_light': '#334155',
    'text_primary': '#F8FAFC',
    'text_secondary': '#CBD5E1',
    'accent': '#8B5CF6',
    'camera_bg': '#111827',
    'border': '#374151'
}

class ModernImageFeedback(ttk_modern.Frame):
    def __init__(self, parent, config, feedback_livestream_image_q):
        super().__init__(parent, style='Section.TFrame')
        
        self.parent = parent
        self.config = config
        self.feedback_livestream_image_q = feedback_livestream_image_q
        self.livestream_image = None
        
        # Camera specifications - optimized for 400px app width
        self.camera_resolution = (300, 450)  # Width x Height
        self.aspect_ratio = 300 / 450  # 0.667 (portrait)
        
        # Display settings optimized for 400px app width (leave margins for UI)
        self.display_width = 280   # Optimized for 400px app width with margins
        self.display_height = 420  # Maintains aspect ratio (280 * 1.5)
        
        # Animation state
        self.pulse_alpha = 0
        self.pulse_direction = 1
        self.scanning_position = 0
        self.is_scanning = False
        
        # Check PIL version for compatibility
        self.setup_pil_compatibility()
        
        self.init_compact_ui_for_400px()
        self.poll_image_loop()

    def setup_pil_compatibility(self):
        """Setup PIL compatibility for different versions"""
        try:
            # Try new Pillow API (9.1.0+)
            self.resample_filter = Image.Resampling.LANCZOS
        except AttributeError:
            try:
                # Try older Pillow API (pre-9.1.0)
                self.resample_filter = Image.LANCZOS
            except AttributeError:
                # Fallback for very old versions
                self.resample_filter = Image.ANTIALIAS
        
        LOGGER.info(f"Using PIL resample filter: {self.resample_filter}")

    def init_compact_ui_for_400px(self):
        """Initialize compact UI optimized for 400px app width"""
        # Configure the frame
        self.configure(style='Section.TFrame')
        
        # Compact status header
        header_frame = tk.Frame(self, bg=MODERN_COLORS['surface'], height=25)  # Reduced height
        header_frame.pack(fill=X, pady=(0, 5))  # Reduced spacing
        header_frame.pack_propagate(False)
        
        # Single row with essential info only
        status_row = tk.Frame(header_frame, bg=MODERN_COLORS['surface'])
        status_row.pack(fill=BOTH, expand=True, padx=5, pady=3)
        
        # Status indicator (left side) - more compact
        self.status_frame = tk.Frame(status_row, bg=MODERN_COLORS['surface'])
        self.status_frame.pack(side=LEFT)
        
        self.status_dot = tk.Label(
            self.status_frame,
            text="●",
            font=('Segoe UI', 10),  # Smaller font
            bg=MODERN_COLORS['surface'],
            fg=MODERN_COLORS['success']
        )
        self.status_dot.pack(side=LEFT, padx=(0, 3))  # Reduced spacing
        
        self.status_text = tk.Label(
            self.status_frame,
            text="LIVE",
            font=('Segoe UI', 8, 'bold'),  # Smaller font
            bg=MODERN_COLORS['surface'],
            fg=MODERN_COLORS['text_secondary']
        )
        self.status_text.pack(side=LEFT)
        
        # Essential info only (right side)
        info_frame = tk.Frame(status_row, bg=MODERN_COLORS['surface'])
        info_frame.pack(side=RIGHT)
        
        self.resolution_label = tk.Label(
            info_frame,
            text="300x450",  # Show actual camera resolution
            font=('Segoe UI', 7),  # Smaller font
            bg=MODERN_COLORS['surface'],
            fg=MODERN_COLORS['text_secondary']
        )
        self.resolution_label.pack(side=RIGHT)
        
        # Camera container - optimized for 400px width
        self.camera_container = tk.Frame(self, bg=MODERN_COLORS['surface'])
        self.camera_container.pack(fill=X, pady=(0, 5))  # Reduced spacing
        
        # Create camera frame with compact size optimized for 400px app width
        self.camera_frame = tk.Frame(
            self.camera_container,
            bg=MODERN_COLORS['camera_bg'],
            relief='flat',
            bd=0,
            highlightbackground=MODERN_COLORS['border'],
            highlightthickness=2,
            width=self.display_width,   # 280px - fits well in 400px app
            height=self.display_height  # 420px - maintains aspect ratio
        )
        self.camera_frame.pack(pady=3)  # Reduced spacing
        self.camera_frame.pack_propagate(False)  # Maintain fixed size
        
        # Camera display label
        self.lbl_image = tk.Label(
            self.camera_frame,
            text="🎥 Initializing Camera...\n300x450 → 280x420",
            bg=MODERN_COLORS['camera_bg'],
            fg=MODERN_COLORS['text_secondary'],
            font=('Segoe UI', 10),  # Smaller font for compact design
            compound='center'
        )
        self.lbl_image.pack(fill=BOTH, expand=True)
        
        # Overlay frame for scanning animation
        self.overlay_frame = tk.Frame(
            self.camera_frame,
            bg=MODERN_COLORS['primary'],
            height=2  # Thinner line for compact design
        )
        # Initially hidden
        
        # Compact detection info panel
        self.detection_info = tk.Frame(self, bg=MODERN_COLORS['surface_light'], height=40)  # Fixed compact height
        self.detection_info.pack(fill=X, pady=(0, 3))  # Reduced spacing
        self.detection_info.pack_propagate(False)
        
        self.init_compact_detection_info_panel()

    def init_compact_detection_info_panel(self):
        """Initialize compact detection information panel for 400px width"""
        info_content = tk.Frame(self.detection_info, bg=MODERN_COLORS['surface_light'])
        info_content.pack(fill=BOTH, expand=True, padx=8, pady=3)  # Reduced padding
        
        # Detection status - single line, compact
        self.detection_status = tk.Label(
            info_content,
            text=" Ready ",
            font=('Segoe UI', 9, 'bold'),  # Smaller font
            bg=MODERN_COLORS['surface_light'],
            fg=MODERN_COLORS['text_primary'],
            anchor='w'
        )
        self.detection_status.pack(fill=X)
        
        # Single compact info row
        info_row = tk.Frame(info_content, bg=MODERN_COLORS['surface_light'])
        info_row.pack(fill=X, pady=(2, 0))  # Reduced spacing
        
        # Essential info only - more compact
        # self.face_count_label = tk.Label(
        #     info_row,
        #     text="Faces: 0",
        #     font=('Segoe UI', 8),  # Smaller font
        #     bg=MODERN_COLORS['surface_light'],
        #     fg=MODERN_COLORS['text_secondary']
        # )
        # self.face_count_label.pack(side=LEFT)
        
        # Processing time on the right
        # self.process_time_label = tk.Label(
        #     info_row,
        #     text="--ms",
        #     font=('Segoe UI', 8),  # Smaller font
        #     bg=MODERN_COLORS['surface_light'],
        #     fg=MODERN_COLORS['text_secondary']
        # )
        # self.process_time_label.pack(side=RIGHT)

    def resize_and_display_image(self, pil_image):
        """Resize image optimized for 400px app width (280px display)"""
        try:
            img_width, img_height = pil_image.size
            
            # Log actual image dimensions for debugging
            LOGGER.debug(f"Received image size: {img_width}x{img_height}")
            
            # Check if image matches expected camera resolution
            if (img_width, img_height) == self.camera_resolution:
                # Perfect match - scale to fit 280x420 display
                scale_factor = min(self.display_width / img_width, self.display_height / img_height)
                new_width = int(img_width * scale_factor)
                new_height = int(img_height * scale_factor)
                
                LOGGER.debug(f"Perfect resolution match, scaling to: {new_width}x{new_height}")
                
            elif img_width == 450 and img_height == 300:
                # Image is rotated - need to rotate it first
                LOGGER.info("Detected rotated image (450x300), rotating to correct orientation")
                pil_image = pil_image.rotate(90, expand=True)
                img_width, img_height = pil_image.size
                
                # Now scale the rotated image
                scale_factor = min(self.display_width / img_width, self.display_height / img_height)
                new_width = int(img_width * scale_factor)
                new_height = int(img_height * scale_factor)
                
            else:
                # Different resolution - scale to fit while maintaining aspect ratio
                scale_w = self.display_width / img_width
                scale_h = self.display_height / img_height
                scale = min(scale_w, scale_h) * 0.95  # 95% to leave some padding
                
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                
                LOGGER.debug(f"Scaling non-standard resolution to: {new_width}x{new_height}")
            
            # Resize image with high quality
            resized_image = pil_image.resize((new_width, new_height), self.resample_filter)
            
            # Add padding if needed to center the image
            if new_width < self.display_width or new_height < self.display_height:
                # Create a new image with the display size and center the resized image
                centered_image = Image.new('RGB', (self.display_width, self.display_height), (17, 24, 39))  # Dark background
                
                # Calculate position to center the image
                x_offset = (self.display_width - new_width) // 2
                y_offset = (self.display_height - new_height) // 2
                
                # Paste the resized image onto the centered background
                centered_image.paste(resized_image, (x_offset, y_offset))
                resized_image = centered_image
            
            # Convert to PhotoImage
            photo_image = ImageTk.PhotoImage(resized_image)
            
            # Store reference and display
            self.livestream_image = photo_image
            self.lbl_image.configure(image=photo_image, text="")
            
            # Store for potential future operations
            self.current_pil_image = pil_image
            
            # Update resolution display
            self.resolution_label.configure(text=f"{self.camera_resolution[0]}x{self.camera_resolution[1]}")
            
        except Exception as e:
            LOGGER.error(f"Error resizing image: {e}")
            self.set_error_state("Image Display Error")

    def poll_image_loop(self):
        """Poll for images on the main GUI thread"""
        try:
            while True:
                image_from_queue = self.feedback_livestream_image_q.get_nowait()
                
                if isinstance(image_from_queue, ImageTk.PhotoImage):
                    # Already a PhotoImage - use directly (fallback)
                    self.livestream_image = image_from_queue
                    self.lbl_image.configure(image=image_from_queue, text="")
                    
                elif isinstance(image_from_queue, Image.Image):
                    # PIL Image - resize and convert
                    self.resize_and_display_image(image_from_queue)
                    
                else:
                    LOGGER.warning(f"Unknown image type received: {type(image_from_queue)}")
                    continue

                # Trigger the image set event
                self.event_generate("<<ON_IMAGE_FEEDBACK_SET>>")
                
                # Update status to show live feed
                self.update_status_indicator(True)

                # Clear remaining image queue
                with self.feedback_livestream_image_q.mutex:
                    self.feedback_livestream_image_q.queue.clear()

        except queue.Empty:
            pass
        except Exception as e:
            LOGGER.error(f"Error in poll_image_loop: {e}")
            self.set_error_state("Camera Feed Error")
        finally:
            # Continue polling
            self.after(self.config.fps_in_millisecond, self.poll_image_loop)

    def update_status_indicator(self, is_live=True):
        """Update the status indicator"""
        if is_live:
            self.status_dot.configure(fg=MODERN_COLORS['success'])
            self.status_text.configure(text="LIVE")
            self.animate_pulse()
        else:
            self.status_dot.configure(fg=MODERN_COLORS['danger'])
            self.status_text.configure(text="OFF")

    def animate_pulse(self):
        """Animate the status indicator pulse"""
        try:
            # Simple pulse animation for the status dot
            colors = [MODERN_COLORS['success'], '#22c55e', MODERN_COLORS['success']]
            color_index = int(self.pulse_alpha / 33) % len(colors)
            self.status_dot.configure(fg=colors[color_index])
            
            self.pulse_alpha += self.pulse_direction * 10
            if self.pulse_alpha >= 100:
                self.pulse_direction = -1
            elif self.pulse_alpha <= 0:
                self.pulse_direction = 1
                
            # Continue animation
            self.after(100, self.animate_pulse)
            
        except Exception as e:
            LOGGER.debug(f"Pulse animation error: {e}")

    def start_scanning_animation(self):
        """Start scanning line animation"""
        self.is_scanning = True
        self.scanning_position = 0
        
        # Show overlay
        self.overlay_frame.place(x=0, y=0, relwidth=1, height=2)  # Thinner line
        self.overlay_frame.configure(bg=MODERN_COLORS['primary'])
        
        # Update detection status
        self.detection_status.configure(
            text=" Scanning... (280x420)",
            fg=MODERN_COLORS['primary']
        )
        
        self.animate_scanning()

    def animate_scanning(self):
        """Animate scanning line"""
        if not self.is_scanning:
            return
            
        try:
            # Move scanning line
            self.scanning_position += 5
            if self.scanning_position > self.display_height:
                self.scanning_position = 0
            
            # Update position
            self.overlay_frame.place(x=0, y=self.scanning_position, relwidth=1, height=2)
            
            # Continue animation
            self.after(50, self.animate_scanning)
            
        except Exception as e:
            LOGGER.debug(f"Scanning animation error: {e}")

    def stop_scanning_animation(self):
        """Stop scanning animation"""
        self.is_scanning = False
        self.overlay_frame.place_forget()

    def update_detection_info(self, face_count=0, confidence=None, process_time=None):
        """Update detection information panel"""
        # # Update face count
        # self.face_count_label.configure(text=f"Faces: {face_count}")
        
        # # Update process time (simplified for compact design)
        # if process_time is not None:
        #     self.process_time_label.configure(text=f"{process_time*1000:.0f}ms")
        # else:
        #     self.process_time_label.configure(text="--ms")
        pass

    def set_loading_state(self):
        """Set the display to show loading state"""
        self.lbl_image.configure(
            text="🎥 Initializing Camera...\n300x450 → 280x420",
            image="",
            bg=MODERN_COLORS['camera_bg'],
            fg=MODERN_COLORS['text_secondary']
        )
        self.livestream_image = None
        self.update_status_indicator(False)
        self.detection_status.configure(
            text="⏳ Initializing... (280x420)",
            fg=MODERN_COLORS['warning']
        )

    def set_error_state(self, error_message="Camera Error"):
        """Set the display to show error state"""
        self.lbl_image.configure(
            text=f" {error_message}\nExpected: 300x450",
            image="",
            bg=MODERN_COLORS['camera_bg'],
            fg=MODERN_COLORS['danger']
        )
        self.livestream_image = None
        self.update_status_indicator(False)
        self.detection_status.configure(
            text=f" {error_message}",
            fg=MODERN_COLORS['danger']
        )

    def set_success_state(self, message="Auth Success", employee_id=None):
        """Set success state with green border"""
        self.camera_frame.configure(highlightbackground=MODERN_COLORS['success'])
        
        success_text = f" {message}"
        if employee_id:
            success_text += f" - {employee_id}"
            
        self.detection_status.configure(
            text=success_text,
            fg=MODERN_COLORS['success']
        )
        
        # Reset after 3 seconds
        self.after(3000, lambda: self.reset_state())

    def set_failure_state(self, message="Auth Failed"):
        """Set failure state with red border"""
        self.camera_frame.configure(highlightbackground=MODERN_COLORS['danger'])
        
        self.detection_status.configure(
            text=f" {message}",
            fg=MODERN_COLORS['danger']
        )
        
        # Reset after 3 seconds
        self.after(3000, lambda: self.reset_state())

    def set_processing_state(self, message="Processing..."):
        """Set processing state with blue border and scanning animation"""
        self.camera_frame.configure(highlightbackground=MODERN_COLORS['primary'])
        
        self.detection_status.configure(
            text=f"⏳ {message}",
            fg=MODERN_COLORS['primary']
        )
        
        self.start_scanning_animation()

    def reset_state(self):
        """Reset to normal state"""
        self.camera_frame.configure(highlightbackground=MODERN_COLORS['border'])
        self.stop_scanning_animation()
        
        self.detection_status.configure(
            text=" Ready ",
            fg=MODERN_COLORS['text_primary']
        )

    def set_face_detected_state(self, face_count=1):
        """Set state when faces are detected"""
        self.detection_status.configure(
            text=f"👤 {face_count} Face{'s' if face_count != 1 else ''} (280x420)",
            fg=MODERN_COLORS['info']
        )
        
        self.update_detection_info(face_count=face_count)

    def clear_image(self):
        """Clear the current image and reset to loading state"""
        self.set_loading_state()

    def get_current_image(self):
        """Get the current displayed image"""
        return self.livestream_image

    def update_config(self, new_config):
        """Update configuration"""
        self.config = new_config

    def get_display_dimensions(self):
        """Get the current display dimensions optimized for 400px app width"""
        return self.display_width, self.display_height  # 280x420

    def get_app_width_optimized_dimensions(self):
        """Get dimensions info for 400px app width"""
        return {
            'app_width': 400,
            'camera_display_width': self.display_width,    # 280
            'camera_display_height': self.display_height,  # 420
            'camera_source_width': self.camera_resolution[0],   # 300
            'camera_source_height': self.camera_resolution[1],  # 450
            'margin_left_right': (400 - self.display_width) // 2,  # ~60px each side
            'compact_design': True
        }

    def show_compact_info(self):
        """Show compact resolution information for 400px app"""
        info = self.get_app_width_optimized_dimensions()
        info_text = f"App: {info['app_width']}px | Cam: {info['camera_display_width']}x{info['camera_display_height']}"
        
        self.detection_status.configure(text=f"📐 {info_text}")
        
        # Reset after 3 seconds
        self.after(3000, lambda: self.reset_state())

    # Additional compact methods for 400px width optimization
    def minimize_ui_elements(self):
        """Further minimize UI elements if needed for very compact display"""
        # Hide resolution label if space is needed
        self.resolution_label.pack_forget()
        
    def restore_ui_elements(self):
        """Restore minimized UI elements"""
        # Restore resolution label
        self.resolution_label.pack(side=RIGHT)