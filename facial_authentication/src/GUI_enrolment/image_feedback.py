import threading
import tkinter as tk
import queue
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

		self.spawn_image_poller_thread()

	def spawn_image_poller_thread(self):
		def _poll_image_loop():
			try:
				# Continuously retrieve and set all image frames from the image queue into the GUI
				# 	until a queue.Empty exception is thrown when all images are cleared from the queue
				while True:
					# Use of get_nowait() to purposely throw a "queue.Empty" exception when image frames are cleared
					# 	from the image queue
					image = self.feedback_livestream_image_q.get_nowait()

					# If we reach here, exception is not thrown (image is available)

					# Assign retrieved image to an attribute to prevent the image from disappearing
					# 	in the GUI (garbage collected)
					self.livestream_image = image

					# Display image
					self.lbl_image.configure(image=image)

					# https://stackoverflow.com/a/49216638/11537143
					# In order to get the latest correct size of a widget, update must be called! This is VERY important and critical!!
					# self.update()
					# custom_logger.get_logger().debug(f'{self.lbl_image.winfo_width()}x{self.lbl_image.winfo_height()}')
					self.event_generate("<<ON_IMAGE_FEEDBACK_SET>>")

					# Clear remaining image queue to be displayed so the next one displayed will be the latest
					# Reference: https://stackoverflow.com/a/6518011/11537143
					with self.feedback_livestream_image_q.mutex:
						self.feedback_livestream_image_q.queue.clear()
					# self.processed_image_q.queue.clear()
			# On empty image queue, an exception is thrown, so catch it
			except queue.Empty:
				# Pass execution to finally clause
				pass
			# Finally clause will always be executed because of except clause
			finally:
				# Give up thread's time slice back to the CPU so the processor is not tied up unnecessarily.
				# 	Then based on the set milliseconds, restart the image polling process so the thread doesn't die off
				self.parent.after(self.config.fps_in_millisecond, _poll_image_loop)
		threading.Thread(target=_poll_image_loop, daemon=True).start()


def main():
	from configuration.app_hybrid_config import _AppConfiguration
	root = tk.Tk()
	img_f = ImageFeedback(root, _AppConfiguration(), queue.Queue())
	img_f.pack(side="top", fill="both", expand=True)
	img_f.spawn_image_poller_thread()
	root.mainloop()


if __name__ == "__main__":
	main()
