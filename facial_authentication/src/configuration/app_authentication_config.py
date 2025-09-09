from pathlib import Path
import serial.tools.list_ports
import sys
import src.logger.custom_logger as custom_logger
LOGGER = custom_logger.get_logger()


class _AppConfiguration:
	def __init__(self):
		# TODO: target properties for PSMS etc page:
		# x = 1537
		# y = 615
		# image size x = 166
		# image size y = 250

		# TODO: Replace below with configurations retrieved from DB
		config = {
			"PORT": _AppConfiguration.get_camera_port(),

			# The min required score authenticating faces must hit to get a match
			"min_auth_score_threshold": 1000, #2600

			# Lower value = slower video stream rate
			"frames_per_second": 64, #120

			# The image size that is displayed in the GUI window
			# X is always 66.66 percent of Y!
			# 0.6666*338 = 225
			"image_feedback_size_x": 400,
			"image_feedback_size_y": 600,

			# Turn on to resize GUI to fit PSMS etc page standards
			"gui_resize_to_fit_enabled": True,

			"debug_app_size_printout_enabled": False,
			"debug_msg_bar_enabled": False,
			"debug_toggle_border_color_enabled": False,
		}
		# Dynamic calculation
		config["fps_in_millisecond"] = int(1000/config["frames_per_second"])
		if config.get("gui_resize_to_fit_enabled"):
			config.update({
				# "image_feedback_size_x": 166,
				# "image_feedback_size_y": 250
				"image_feedback_size_x": 300,
				"image_feedback_size_y": 450
			})

		self.config = config

	def __getattr__(self, name):
		try:
			return self.config[name]
		except KeyError:
			print(f'_AppConfiguration Warning: {name} config does not exist, defaulting to None')
			return None

	@staticmethod
	def __debug_camera_info():
		import json
		from datetime import date, datetime

		dump_data = []
		Path("log/device/").mkdir(parents=True, exist_ok=True)
		with open("log/device/device_tracing.json", "a+") as json_file:
			json_file.seek(0)
			try:
				dump_data = json.load(json_file)
			except:
				pass

		debug_ports = serial.tools.list_ports.comports()
		for debug_port in debug_ports:
			_dict = debug_port.__dict__
			if 'Bluetooth' not in debug_port.description:
				_dict["connection_date"] = date.today().strftime("%d/%m/%y")
				_dict["connection_time"] = datetime.now().strftime("%H:%M:%S")
				dump_data.append(_dict)

		with open("log/device/device_tracing.json", "w", encoding='utf-8') as json_file:
			json.dump(dump_data, json_file, ensure_ascii=False, indent=4, default=str)

	@staticmethod
	def get_camera_port():
		_AppConfiguration.__debug_camera_info()

		ports = serial.tools.list_ports.comports()
		com_port = None
		for port in ports:
			if 'USB VID:PID=2AAD:6373' in port.hwid:
				com_port = port.device

		if com_port is None:
			LOGGER.error("No Intel F455 camera device detected on the system! Program exiting.")
			sys.exit()

		return com_port
