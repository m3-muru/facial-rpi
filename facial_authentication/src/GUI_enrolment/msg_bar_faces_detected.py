import tkinter as tk
import threading
import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class FacesDetetectedMsgBar(tk.Frame):
	def __init__(self, parent, faces_detected_feedback_q):
		tk.Frame.__init__(self, parent)
		self.parent = parent
		self.faces_detected_feedback_q = faces_detected_feedback_q

		self.feedback_string = tk.StringVar()

		self.lbl_feedback = ttk.Label(
			self, textvariable=self.feedback_string,
			font='Helvetica 10 bold', anchor=CENTER, relief=SUNKEN, borderwidth=3,
			width=48
		)
		self.lbl_feedback.pack(ipady=5, ipadx=5, pady=5, padx=5)

		self.poll_feedback_q()

	def set_feedback_msg(self, msg):
		self.feedback_string.set(msg)

	def poll_feedback_q(self):
		def _poll_feedback_q():
			nonlocal self
			feedback_msg = self.faces_detected_feedback_q.get()
			if feedback_msg:
				self.set_feedback_msg(feedback_msg)
			else:
				self.set_feedback_msg('Face Detector Ready')
			_poll_feedback_q()

		threading.Thread(target=_poll_feedback_q, daemon=True).start()
