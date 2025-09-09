import tkinter as tk
# from PIL import Image, ImageTk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class EnrollPopupWindow(tk.Toplevel):
	def __init__(self, parent):
		tk.Toplevel.__init__(self, parent)
		self.wm_title('Enroll Employee')

		# Logic to position popup window relative to parent window
		x = parent.parent.winfo_x()
		y = parent.parent.winfo_y()
		self.geometry("%dx%d+%d+%d" % (400, 150, x+1, y+50))

		self.tkraise(parent)

		# Force popup window to become main, disables the parent window from interaction
		self.grab_set()

		tk.Label(self, text="Enter Employee ID", font='Helvetica 12 bold').pack(side="top")

		self.emp_id_tk_str_var = tk.StringVar()
		employee_id_entry = tk.Entry(self, textvariable=self.emp_id_tk_str_var, width=20)
		employee_id_entry.pack(ipady=5)
		employee_id_entry.focus()

		okay_btn = ttk.Button(
			self, text="Okay", command=self.cleanup, bootstyle="primary", width=25
		)
		okay_btn.pack(pady=5, ipady=5)

		# Register "enter" key event to the popup window
		self.bind('<Return>', (lambda event: self.cleanup()))

		# Register "esc" key event to the popup window
		self.bind('<Escape>', (lambda event: self.close()))

	def close(self):
		self.clear_inputs()
		self.cleanup()

	def get_input(self):
		# TODO: perform additional cleaning of input here if required
		cleaned_emp_id = self.emp_id_tk_str_var.get().strip()
		return cleaned_emp_id

	def clear_inputs(self):
		self.emp_id_tk_str_var.set('')

	def cleanup(self):
		self.destroy()
