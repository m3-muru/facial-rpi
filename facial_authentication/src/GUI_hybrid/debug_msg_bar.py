import tkinter as tk
import threading


class DebugMsgBar(tk.Frame):
	def __init__(self, parent):
		tk.Frame.__init__(self, parent)
		self.parent = parent

		self.feedback_string = tk.StringVar()

		self.lbl_feedback = tk.Label(self, textvariable=self.feedback_string, font='Helvetica 12 bold')
		self.lbl_feedback.pack()

	def set_feedback(self, feedback):
		self.feedback_string.set(feedback)
