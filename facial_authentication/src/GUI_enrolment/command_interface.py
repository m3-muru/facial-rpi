import queue
import threading
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from src.GUI_enrolment.enroll_popup_window import EnrollPopupWindow
import src.logger.custom_logger as custom_logger

LOGGER = custom_logger.get_logger()


class CommandInterface(tk.Frame):
	def __init__(self, parent, config, cmd_request_q, ready_status_q):
		tk.Frame.__init__(self, parent)
		self.parent = parent
		self.config = config
		self.cmd_request_q = cmd_request_q
		self.ready_status_q = ready_status_q
		self.btn_enroll = ttk.Button(
			self, text="Enroll", command=self.popup_enroll_window,
			bootstyle="primary", width=20
		)
		self.btn_enroll.pack(side=LEFT, padx=10, pady=5, ipady=5)

		self.btn_quit = ttk.Button(
			self, text="Quit", command=lambda: self.parent.quit_app(),
			bootstyle="secondary", width=20
		)
		self.btn_quit.pack(pady=5, ipady=5)

		# Register "enter" key event to the root window
		self.parent.parent.bind('<Return>', (lambda event: self.popup_enroll_window()))

		# Register "esc" key event to the root window
		self.parent.parent.bind('<Escape>', (lambda event: self.parent.quit_app()))

		self.parent.parent.bind('<<ON_APP_ALIGNED>>', (lambda event: self.focus_on_primary_btn()))

		self.spawn_ready_status_poller_thread()

	def focus_on_primary_btn(self):
		self.btn_enroll.focus()

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

	def popup_enroll_window(self):
		enroll_popup_win = EnrollPopupWindow(self.parent)
		enroll_popup_win.protocol("WM_DELETE_WINDOW", enroll_popup_win.close)

		self.disable()
		self.wait_window(enroll_popup_win)
		self.enable()

		employee_id = enroll_popup_win.get_input()
		print(f'Received employee_id: |{employee_id}|')
		# If employee ID provided is not blank or filled with whitespaces only, then perform enrolment
		if employee_id:
			self.put_command_request('enrol', employee_id)

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
		self.parent.parent.bind('<Return>', (lambda event: self.popup_enroll_window()))
		self.parent.parent.bind('<Escape>', (lambda event: self.parent.quit_app()))

	def put_command_request(self, command, employee_id=None):
		# Rebind return button behaviour to ignore key events to prevent enrolment spam
		self.ignore_all_bindings()

		request_dict = {
			"command": command,
			"employee_id": employee_id
		}
		self.cmd_request_q.put(request_dict)

		# Reinstate return button behaviour to process key events
		self.parent.after(3000, lambda: self.reinstate_all_bindings())
