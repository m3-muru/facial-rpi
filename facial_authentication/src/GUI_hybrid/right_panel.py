import tkinter as tk
from GUI_hybrid.image_feedback import ImageFeedback
from GUI_hybrid.status_msg_bar import StatusMsgBar
from GUI_hybrid.instruction_msg_bar import InstructionMsgBar
from GUI_hybrid.debug_msg_bar import DebugMsgBar  # TODO: Remove debugger


class RightPanelFrame(tk.Frame):
	def __init__(self, parent, config, processed_image_q, feedback_q, instruction_msg_q):
		tk.Frame.__init__(self, parent)
		self.debug_color = "#000000"  # black

		# Panel contents creation
		self.image_feedback_frame = ImageFeedback(self, config, processed_image_q)
		self.image_feedback_frame.debug_color = "#00cc00"  # green

		self.status_msg_bar = StatusMsgBar(self, feedback_q)
		self.status_msg_bar.debug_color = "#33FFF3"  # teal

		self.instruction_msg_bar = InstructionMsgBar(self, instruction_msg_q)
		self.instruction_msg_bar.debug_color = "#6E2111"  # Dark red

		self.debug_msg_bar = DebugMsgBar(self)  # TODO: Remove debugger
		self.debug_msg_bar.debug_color = "#FE00EF"  # Pink

		# Panel contents placement and positioning
		self.pack(side=tk.LEFT)
		self.image_feedback_frame.pack(side=tk.TOP)
		self.status_msg_bar.pack()
		self.instruction_msg_bar.pack()
		self.debug_msg_bar.pack()  # TODO: Remove debugger
