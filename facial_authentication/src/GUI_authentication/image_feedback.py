import threading
import tkinter as tk
import queue
from PIL import Image, ImageTk
import src.logger.custom_logger as custom_logger

LOGGER = custom_logger.get_logger()


class ImageFeedback(tk.Frame):
    def __init__(self, parent, config, feedback_livestream_image_q):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.config = config
        self.feedback_livestream_image_q = feedback_livestream_image_q
        self.configure(width=self.config.image_feedback_size_x, height=self.config.image_feedback_size_y)
        self.livestream_image = None  # Required to ensure image isn't garbage collected

        self.lbl_image = tk.Label(self, text="Image preview starting...")
        self.lbl_image.pack()

        # Start polling on main thread instead of background thread
        self.poll_image_loop()

    def poll_image_loop(self):
        """
        Poll for images on the main GUI thread (thread-safe)
        """
        try:
            # Continuously retrieve and set all image frames from the image queue into the GUI
            # until a queue.Empty exception is thrown when all images are cleared from the queue
            while True:
                # Use of get_nowait() to purposely throw a "queue.Empty" exception when image frames are cleared
                # from the image queue
                image_from_queue = self.feedback_livestream_image_q.get_nowait()

                # If we reach here, exception is not thrown (image is available)
                
                # Handle different image types
                if isinstance(image_from_queue, ImageTk.PhotoImage):
                    # Already a PhotoImage - use directly
                    processed_image = image_from_queue
                elif isinstance(image_from_queue, Image.Image):
                    # PIL Image - convert to PhotoImage (safe on main thread)
                    processed_image = ImageTk.PhotoImage(image_from_queue)
                else:
                    LOGGER.warning(f"Unknown image type received: {type(image_from_queue)}")
                    continue

                # Assign retrieved image to an attribute to prevent the image from disappearing
                # in the GUI (garbage collected)
                self.livestream_image = processed_image

                # Display image (this is now safe because we're on the main thread)
                self.lbl_image.configure(image=processed_image, text="")

                # Trigger the image set event
                self.event_generate("<<ON_IMAGE_FEEDBACK_SET>>")

                # Clear remaining image queue to be displayed so the next one displayed will be the latest
                # Reference: https://stackoverflow.com/a/6518011/11537143
                with self.feedback_livestream_image_q.mutex:
                    self.feedback_livestream_image_q.queue.clear()

        # On empty image queue, an exception is thrown, so catch it
        except queue.Empty:
            # Pass execution to finally clause
            pass
        except Exception as e:
            LOGGER.error(f"Error in poll_image_loop: {e}")
            # Set error state
            self.lbl_image.configure(
                text="Camera Feed Error",
                image="",
                bg="red",
                fg="white"
            )
        # Finally clause will always be executed because of except clause
        finally:
            # Give up thread's time slice back to the CPU so the processor is not tied up unnecessarily.
            # Then based on the set milliseconds, restart the image polling process so the thread doesn't die off
            self.parent.after(self.config.fps_in_millisecond, self.poll_image_loop)

    def spawn_image_poller_thread(self):
        """
        Legacy method for backward compatibility - now just calls the main thread version
        """
        LOGGER.warning("spawn_image_poller_thread() called - using main thread polling instead")
        # Don't start a new thread, polling is already running on main thread

    def set_loading_state(self):
        """
        Set the display to show loading state
        """
        self.lbl_image.configure(
            text="Image preview starting...",
            image="",
            bg="black",
            fg="white"
        )
        self.livestream_image = None

    def set_error_state(self, error_message="Camera Error"):
        """
        Set the display to show error state
        """
        self.lbl_image.configure(
            text=error_message,
            image="",
            bg="red",
            fg="white"
        )
        self.livestream_image = None

    def clear_image(self):
        """
        Clear the current image and reset to loading state
        """
        self.set_loading_state()

    def get_current_image(self):
        """
        Get the current displayed image
        """
        return self.livestream_image

    def update_config(self, new_config):
        """
        Update configuration and resize accordingly
        """
        self.config = new_config
        self.configure(width=self.config.image_feedback_size_x, height=self.config.image_feedback_size_y)


def main():
    try:
        from src.configuration.app_authentication_config import _AppConfiguration
    except ImportError:
        # Fallback for testing
        class _AppConfiguration:
            def __init__(self):
                self.image_feedback_size_x = 640
                self.image_feedback_size_y = 480
                self.fps_in_millisecond = 50

    root = tk.Tk()
    root.title("ImageFeedback Test")
    
    config = _AppConfiguration()
    test_queue = queue.Queue()
    
    img_f = ImageFeedback(root, config, test_queue)
    img_f.pack(side="top", fill="both", expand=True)
    
    # Test with a sample image after 2 seconds
    def test_image():
        try:
            # Create a test PIL image
            test_img = Image.new('RGB', (config.image_feedback_size_x, config.image_feedback_size_y), color='blue')
            test_queue.put(test_img)
        except Exception as e:
            LOGGER.error(f"Error creating test image: {e}")
    
    root.after(2000, test_image)  # Test after 2 seconds
    root.mainloop()


if __name__ == "__main__":
    main()