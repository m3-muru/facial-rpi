import tkinter as tk
# from PIL import Image, ImageTk


class EmpIDEnrollPopupWindow(tk.Toplevel):
	def __init__(self, parent):
		tk.Toplevel.__init__(self, parent)
		self.wm_title('Enroll user')
		self.geometry(f'480x640')
		self.tkraise(parent)

		# self.image_tk = ImageTk.PhotoImage(Image.open(r"image/begin_scan.jpg"))
		# tk.Label(self, image=self.image_tk).pack(side="top", fill="x", pady=10)

		tk.Label(self, text="Enter employee ID").pack(side="top", fill="x", pady=10)

		self.emp_id_tk_str_var = tk.StringVar()
		tk.Entry(self, textvariable=self.emp_id_tk_str_var, width=20).pack()

		tk.Button(self, text="Okay", command=self.cleanup).pack()

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
