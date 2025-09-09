import threading
import tkinter as tk
from PIL import Image, ImageTk
import queue


class ImageFeedback(tk.Frame):
	def __init__(self, parent, config, processed_image_q):
		tk.Frame.__init__(self, parent)
		self.parent = parent
		self.config = config
		self.processed_image_q = processed_image_q
		self.configure(width=self.config.image_feedback_size_x, height=self.config.image_feedback_size_y)
		self.image_livestream = None  # Required to ensure image isn't garbage collected

		self.image_instruction = ImageTk.PhotoImage(Image.open(r"image/begin_scan.jpg"))
		self.lbl_image = tk.Label(self, image=self.image_instruction)
		self.lbl_image.pack()

		self.poll_image_loop()

	def poll_image_loop(self):
		def _poll_image_loop():
			try:
				# Continuously retrieve and set all image frames from the image queue into the GUI
				# 	until a queue.Empty exception is thrown when all images are cleared from the queue
				while True:
					try:
						# Update debugger feedback to show how many images are left undisplayed (delay caused)
						self.parent.debug_msg_bar.set_feedback(f'Image in queue: {self.processed_image_q.qsize()}')
					except AttributeError:
						pass
					# Use of get_nowait() to purposely throw a "queue.Empty" exception when image frames are cleared
					# 	from the image queue
					image = self.processed_image_q.get_nowait()

					# If we reach here, exception is not thrown (image is available)

					# Assign retrieved image to an attribute to prevent the image from disappearing
					# 	in the GUI (garbage collected)
					self.image_livestream = image

					# Display image
					self.lbl_image.configure(image=image)

					# Clear remaining image queue to be displayed so the next one displayed will be the latest
					# Reference: https://stackoverflow.com/a/6518011/11537143
					with self.processed_image_q.mutex:
						self.processed_image_q.queue.clear()
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
	img_f.poll_image_loop()
	root.mainloop()


if __name__ == "__main__":
	main()
