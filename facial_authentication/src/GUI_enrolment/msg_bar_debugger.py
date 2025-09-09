import tkinter as tk
import threading


class DebugMsgBar(tk.Frame):
	def __init__(self, parent, config):
		tk.Frame.__init__(self, parent)
		self.parent = parent
		self.config = config

		self.feedback_string = tk.StringVar()

		self.lbl_feedback = tk.Label(self, textvariable=self.feedback_string, font='Helvetica 12 bold')

		if self.config.debug_msg_bar_enabled:
			self.lbl_feedback.pack()
			self.debug_color = "#FE00EF"  # Pink
			self.pack()  # TODO: Remove debugger
			self.set_feedback("Debug msg ready")

	def set_feedback(self, feedback):
		self.feedback_string.set(feedback)
