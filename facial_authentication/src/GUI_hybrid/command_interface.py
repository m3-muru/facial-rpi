import queue
import threading
import tkinter as tk
from GUI_hybrid.emp_id_enroll_popup_window import EmpIDEnrollPopupWindow


# TODO: add ready_status_q for command_button.py (name it to command_interface.py) to poll
#   and track face processor status, when not ready = disable interface vice versa.
#   Ready status should be updated on auth and init etc
class CommandInterface(tk.Frame):
	def __init__(self, parent, config, cmd_request_q, ready_status_q):
		tk.Frame.__init__(self, parent)
		self.parent = parent
		self.config = config
		self.cmd_request_q = cmd_request_q
		self.ready_status_q = ready_status_q
		self.configure(width=self.config.interface_size_x, height=self.config.interface_size_y)

		self.btn_enroll = tk.Button(self, text="Enroll", command=self.popup_enroll_window, height=5, width=30).pack(pady=5)
		self.btn_authenticate = tk.Button(self, text="Authenticate", command=lambda: self.put_request('a'), height=5, width=30).pack(pady=5)
		self.btn_quit = tk.Button(self, text="Quit", command=lambda: self.put_request('q'), height=5, width=30).pack(pady=5)

		self.debug_color = "#00cc00"  # green

		self.pack_propagate(0)

		self.poll_ready_status()

	def poll_ready_status(self):
		def _poll_ready_status():
			nonlocal self
			is_ready = self.ready_status_q.get()
			if is_ready:
				self.enable()
			else:
				self.disable()
			_poll_ready_status()
		threading.Thread(target=_poll_ready_status, daemon=True).start()

	def popup_enroll_window(self):
		enroll_popup_win = EmpIDEnrollPopupWindow(self.parent)
		enroll_popup_win.protocol("WM_DELETE_WINDOW", enroll_popup_win.close)

		self.disable()
		self.wait_window(enroll_popup_win)
		self.enable()

		employee_id = enroll_popup_win.get_input()
		print(f'Received employee_id: |{employee_id}|')
		# If employee ID provided is not blank or filled with whitespaces only, then perform enrolment
		if employee_id:
			self.put_request('e', employee_id)

	def disable(self):
		for key, value in self.children.items():
			value["state"] = "disabled"

	def enable(self):
		for key, value in self.children.items():
			value["state"] = "normal"

	def put_request(self, key_command, employee_id=None):
		request = {
			"key_character": key_command,
			"key_code": ord(key_command)
		}

		if request.get("key_character") == 'e':
			request["employee_id"] = employee_id

		self.cmd_request_q.put(request)


def main():
	from configuration.app_hybrid_config import _AppConfiguration
	root = tk.Tk()
	CommandInterface(root, _AppConfiguration(), queue.Queue()).pack(side="top", fill="both", expand=True)
	root.mainloop()


if __name__ == "__main__":
	main()
