import tkinter as tk
import threading


class InstructionMsgBar(tk.Frame):
	def __init__(self, parent, instruction_msg_q):
		tk.Frame.__init__(self, parent)
		self.parent = parent
		self.instruction_msg_q = instruction_msg_q

		self.instruction_msg_string = tk.StringVar()

		self.lbl_instruction_msg = tk.Label(self, textvariable=self.instruction_msg_string, font='Helvetica 12 bold')
		self.lbl_instruction_msg.pack()

		self.poll_instruction_msg_q()

	def set_instruction_msg(self, msg):
		self.instruction_msg_string.set(msg)

	def poll_instruction_msg_q(self):
		def _poll_instruction_msg_q():
			nonlocal self
			instruction_msg = self.instruction_msg_q.get()
			if instruction_msg:
				self.set_instruction_msg(instruction_msg)
			else:
				self.set_instruction_msg('Click a button on the left to start')
			_poll_instruction_msg_q()

		threading.Thread(target=_poll_instruction_msg_q, daemon=True).start()
