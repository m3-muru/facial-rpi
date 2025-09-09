import tkinter as tk
import threading

import utility.gui_feedback_color_utility as color_utility


class StatusMsgBar(tk.Frame):
	def __init__(self, parent, feedback_q):
		tk.Frame.__init__(self, parent)
		self.parent = parent

		self.feedback_q = feedback_q

		self.feedback_string = tk.StringVar()

		self.lbl_feedback = tk.Label(self, textvariable=self.feedback_string, font='Helvetica 12 bold')
		self.lbl_feedback.pack()

		self.poll_feedback_q()

	# TODO: this method is not in used, just adding it here as reference for the color code. Code can be removed.
	@staticmethod
	def color_from_msg(msg):
		if 'Success' in msg:
			# Green
			return (0x3c, 0xff, 0x3c)
		if 'Forbidden' in msg or 'Fail' in msg or 'NoFace' in msg:
			# Red
			return (0x3c, 0x3c, 0xFF)
		# Gray
		return (0xcc, 0xcc, 0xcc)

	@staticmethod
	def get_appropriate_status_color(face_process_status):
		# in progress = black, success = green, failure = red
		color = color_utility.get_status_bar_feedback_color(face_process_status)
		return color

	def set_feedback(self, feedback):
		msg = feedback.get("msg")
		self.feedback_string.set(msg)

		face_process_status = feedback.get("face_process_status")
		self.lbl_feedback.configure(fg=self.get_appropriate_status_color(face_process_status))

	def poll_feedback_q(self):
		def _poll_feedback_q():
			nonlocal self
			feedback = self.feedback_q.get()
			self.set_feedback(feedback)
			_poll_feedback_q()

		threading.Thread(target=_poll_feedback_q, daemon=True).start()
