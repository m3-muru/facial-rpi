import tkinter as tk
from GUI_hybrid.command_interface import CommandInterface


class LeftPanelFrame(tk.Frame):
	def __init__(self, parent, config, cmd_request_q, ready_status_q):
		tk.Frame.__init__(self, parent)
		self.debug_color = "#FF5733"  # orange

		# Panel contents creation
		self.cmd_interface_frame = CommandInterface(self, config, cmd_request_q, ready_status_q)

		# Panel contents placement and positioning
		self.pack(side=tk.LEFT)
		self.cmd_interface_frame.pack(side=tk.TOP)
