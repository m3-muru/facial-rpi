import queue
import threading
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import src.logger.custom_logger as custom_logger

LOGGER = custom_logger.get_logger()


class CommandInterface(tk.Frame):
	def __init__(self, parent, config, cmd_request_q, ready_status_q):
		tk.Frame.__init__(self, parent)
		self.parent = parent
		self.config = config
		self.cmd_request_q = cmd_request_q
		self.ready_status_q = ready_status_q

        # Muru: Disable button, use gesture to trigger
		"""
		self.btn_authenticate = ttk.Button(
			self, text="Authenticate", command=lambda: self.put_command_request('authenticate'),
			bootstyle="primary"
		)
		"""

		# self.btn_authenticate = ttk.Button(
		# 	self, text="Start", command=lambda: self.put_command_request('authenticate_with_gesture'),
		# 	bootstyle="primary", width=10
		# )
		#
		# self.btn_authenticate.pack(side=LEFT, padx=5, pady=5, ipady=5)
		#
		# self.btn_resync_faceprint = ttk.Button(
		# 	self, text="Resync", command=lambda: self.put_command_request('resync'),
		# 	bootstyle="info", width=10
		# )
		# self.btn_resync_faceprint.pack(side=LEFT, padx=5, pady=5, ipady=5)

		# self.btn_quit = ttk.Button(
		# 	self, text="Quit", command=lambda: self.parent.quit_app(),
		# 	bootstyle="secondary", width=10
		# )
		# self.btn_quit.pack(side=LEFT, padx=5, pady=5, ipady=5)


		# Register "enter" key event to the root window
		# self.parent.parent.bind('<Return>', (lambda event: self.put_command_request('authenticate')))
		#self.parent.parent.bind('<Return>', (lambda event: self.put_command_request('authenticate_with_gesture')))
		
		self.put_command_request('authenticate')

		# Register "esc" key event to the root window
		self.parent.parent.bind('<Escape>', (lambda event: self.parent.quit_app()))

		#self.parent.parent.bind('<<ON_APP_ALIGNED>>', (lambda event: self.focus_on_primary_btn()))

		self.spawn_ready_status_poller_thread()

	#def focus_on_primary_btn(self):
		#self.btn_authenticate.focus()

	def init_ready_status_q_poller(self):
		def _retrieve_ready_status():
			is_ready = self.ready_status_q.get()
			if is_ready:
				self.enable()
			else:
				self.disable()

		while True:
			_retrieve_ready_status()

	def spawn_ready_status_poller_thread(self):
		threading.Thread(target=self.init_ready_status_q_poller, daemon=True).start()

	def disable(self):
		for key, value in self.children.items():
			value["state"] = "disabled"

	def enable(self):
		for key, value in self.children.items():
			value["state"] = "normal"

	def ignore_all_bindings(self):
		def _ignore_all_bindings(event):
			LOGGER.debug(f'keyboard event binding ignored: {event}')
			return "break"
		self.parent.parent.bind('<Return>', (lambda event: _ignore_all_bindings(event)))
		self.parent.parent.bind('<Escape>', (lambda event: _ignore_all_bindings(event)))

	def reinstate_all_bindings(self):
		#self.parent.parent.bind('<Return>', (lambda event: self.put_command_request('authenticate')))
		self.parent.parent.bind('<Return>', (lambda event: self.put_command_request('authenticate_with_gesture')))
		self.parent.parent.bind('<Escape>', (lambda event: self.parent.quit_app()))

	def put_command_request(self, command):
		# Rebind return button behaviour to ignore key events to prevent authentication spam
		self.ignore_all_bindings()

		request_dict = {
			"command": command
		}

		self.cmd_request_q.put(request_dict)

		# Reinstate return button behaviour to process key events
		self.parent.after(3000, lambda: self.reinstate_all_bindings())
