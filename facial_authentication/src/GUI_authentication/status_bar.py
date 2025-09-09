import tkinter as tk
import threading
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

import src.utility.gui_feedback_color_utility as color_utility
import src.logger.custom_logger as custom_logger

LOGGER = custom_logger.get_logger()


class StatusBar(tk.Frame):
	def __init__(self, parent, feedback_msg_q):
		tk.Frame.__init__(self, parent)
		self.parent = parent

		self.feedback_msg_q = feedback_msg_q

		self.feedback_string = tk.StringVar()

		self.lbl_feedback = ttk.Label(
			self, textvariable=self.feedback_string,
			font='Helvetica 15 bold', anchor=CENTER, relief=SUNKEN, borderwidth=5,
			width=35
		)
		# self.lbl_feedback = tk.Label(
		# 	self, textvariable=self.feedback_string, font='Helvetica 12 bold',
		# 	borderwidth=2, relief="ridge"
		# )
		self.lbl_feedback.pack(ipady=5, ipadx=5, pady=5, padx=5)

		self.spawn_feedback_poller_thread()

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

	def set_msg(self, msg):
		self.feedback_string.set(msg)

	def set_msg_color(self, status):
		self.lbl_feedback.configure(foreground=self.get_appropriate_status_color(status))

	def set_feedback(self, feedback):
		msg = feedback.get("msg")
		self.set_msg(msg)

		status = feedback.get("status")
		self.set_msg_color(status)

	def init_retrieve_feedback_q_poller(self):
		def _retrieve_feedback():
			feedback = self.feedback_msg_q.get()
			self.set_feedback(feedback)

		while True:
			_retrieve_feedback()

    # ETC status enhancement
    def set_etc_status(self, status_type, is_connected, message=None):
        """Set ETC-specific status"""
        if message is None:
            if status_type == "etc_web":
                message = "ETC Web Connected" if is_connected else "ETC Web Disconnected"
            elif status_type == "websocket":
                message = "ETC WebSocket Connected" if is_connected else "ETC WebSocket Issue"
            else:
                message = f"ETC {status_type} {'Connected' if is_connected else 'Disconnected'}"
        
        # Determine status for coloring
        if is_connected:
            status = "success" if "web" in status_type.lower() else "info"
        else:
            status = "danger" if "web" in status_type.lower() else "warning"
        
        # Set the message
        self.set_feedback({"msg": message, "status": status})

	def spawn_feedback_poller_thread(self):
		threading.Thread(target=self.init_retrieve_feedback_q_poller, daemon=True).start()
