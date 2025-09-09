import tkinter as tk
import queue

from src.configuration.app_enrolment_config import _AppConfiguration

import src.utility.gui_window_utility as window_utility

from src.processor.image_processor import ImageProcessor
from src.processor.face_processor import FaceProcessor

from src.GUI_enrolment.command_interface import CommandInterface
from src.GUI_enrolment.image_feedback import ImageFeedback
from src.GUI_enrolment.status_bar import StatusBar
from src.GUI_enrolment.msg_bar_faces_detected import FacesDetetectedMsgBar
from src.GUI_enrolment.msg_bar_debugger import DebugMsgBar  # TODO: Remove debugger

import src.logger.custom_logger as custom_logger

LOGGER = custom_logger.get_logger()


class EnrolmentApplication(tk.Frame):
	def __init__(self, parent):
		tk.Frame.__init__(self, parent)
		self.parent = parent

		# ---Config initialization---
		self.config = _AppConfiguration()

		# ---Communication queues creation---
		self.cmd_request_q = queue.Queue()
		self.ready_status_q = queue.Queue()
		self.feedback_livestream_image_q = queue.Queue()
		self.feedback_livestream_detections_q = queue.Queue()
		# Purpose:
		# 	used for passing message and color of message from face_processor
		# 	to be set in DetectionProgressMsgBar (feedback bar)
		self.feedback_msg_q = queue.Queue()
		self.faces_detected_feedback_q = queue.Queue()

		# ---Processor creation---
		self.image_processor = ImageProcessor(
			self.feedback_livestream_image_q, self.feedback_livestream_detections_q, self.config
		)
		self.face_processor = FaceProcessor(
			self,
			self.cmd_request_q, self.ready_status_q,
			self.feedback_msg_q, self.faces_detected_feedback_q,
			self.feedback_livestream_detections_q, self.config,
			FaceProcessor.MODE_ENROLMENT
		)

		# ---Begin Processors---
		self.begin_image_processing()
		self.begin_face_processing()

		# ---Internal GUI content creation---
		self.image_feedback_frame = ImageFeedback(self, self.config, self.feedback_livestream_image_q)
		self.image_feedback_frame.debug_color = "#00cc00"  # green
		self.image_feedback_frame.pack(side=tk.TOP)

		self.status_bar = StatusBar(self, self.feedback_msg_q)
		self.status_bar.debug_color = "#33FFF3"  # teal
		self.status_bar.pack()

		# TODO: Remove because not required, remember to remove references it uses
		# self.face_detected_msg_bar = FacesDetetectedMsgBar(self, self.faces_detected_feedback_q)
		# self.face_detected_msg_bar.debug_color = "#6E2111"  # Dark red
		# self.face_detected_msg_bar.pack()

		self.cmd_interface_frame = CommandInterface(self, self.config, self.cmd_request_q, self.ready_status_q)
		self.cmd_interface_frame.debug_color = "#FF5733"  # orange
		self.cmd_interface_frame.pack()

		# ---Debugger related---
		self.debug_msg_bar = DebugMsgBar(self, self.config)
		self.debug_toggle_gui_border_color()
		self.parent.bind('<F1>', (lambda event: self.align_app(window_utility.ALIGN_CENTER)))
		self.parent.bind('<F2>', (lambda event: self.align_app(window_utility.ALIGN_BOTTOM_RIGHT)))
		self.parent.bind('<F3>', (lambda event: window_utility.print_window_properties(self.parent)))
		self.parent.bind('<F4>', (lambda event: self.toggle_debug_app_size_printout_enabled()))

		# ---Init root GUI window properties---
		self.init_window_properties()
		self.parent.bind('<<ON_IMAGE_FEEDBACK_SET>>', (lambda event: self.align_app_on_image_feedback_set()))
		self.parent.protocol("WM_DELETE_WINDOW", self.quit_app)

	def exit(self):
		import os
		LOGGER.info(f'Application exiting...')
		os._exit(0)

	def quit_app(self):
		self.status_bar.set_msg('Goodbye~')
		self.after(500, lambda: self.exit())

	def align_app_on_image_feedback_set(self):
		LOGGER.debug('<<ON_IMAGE_FEEDBACK_SET>> event caught')
		self.parent.unbind('<<ON_IMAGE_FEEDBACK_SET>>')
		self.align_app(window_utility.ALIGN_CENTER)

	def align_app(self, alignment):
		window_utility.align_window(self.parent, alignment)
		self.parent.event_generate("<<ON_APP_ALIGNED>>")

	def toggle_debug_app_size_printout_enabled(self):
		self.config.debug_app_size_printout_enabled = False \
			if self.config.debug_app_size_printout_enabled \
			else True
		self.init_debug_app_size_printout()

	def init_debug_app_size_printout(self):
		if self.config.debug_app_size_printout_enabled:
			self.parent.bind('<Configure>', lambda event: window_utility.print_window_properties(self.parent))
		else:
			self.parent.unbind('<Configure>')

	def init_window_properties(self):
		self.parent.title('MavenTree\'s Face Enrolment')

		# Force window to always be on top
		self.parent.attributes("-topmost", True)

	def begin_image_processing(self):
		self.image_processor.start()

	def begin_face_processing(self):
		self.face_processor.start()

	def debug_toggle_gui_border_color(self):
		if self.config.debug_toggle_border_color_enabled:
			def _debug_toggle_border_color(target):
				for key, value in target.children.items():
					try:
						_debug_toggle_border_color(value)
						value.configure(highlightbackground=value.debug_color, highlightthickness=3)
					except:
						pass

			_debug_toggle_border_color(self)


def main():
	LOGGER.info(f'Application starting...')
	root = tk.Tk()
	EnrolmentApplication(root).pack(side="top", fill="both", expand=True)
	root.mainloop()


if __name__ == "__main__":
	main()
