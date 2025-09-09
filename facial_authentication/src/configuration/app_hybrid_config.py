import serial.tools.list_ports
import sys


class _AppConfiguration:
	def __init__(self):
		# TODO: Replace below with configurations retrieved from DB
		config = {
			"PORT": _AppConfiguration.get_camera_port(),
			"livestream_enabled": True,
			"frames_per_second": 120,
			"debug_GUI_interface_enabled": False,
			"window_size_x": 900,
			"window_size_y": 900,
			"min_auth_score_threshold": 3000,  			# The min required score authenticating faces must hit
			"min_long_enroll_score_threshold": 3000,  	# Currently not in use, the min required score enrolling faces
														# 	must hit, if not the app will keep re-enrolling
			"enroll_best_out_of": 3
		}
		config["interface_size_x"] = int(config["window_size_x"] / 2)
		config["interface_size_y"] = int(config["window_size_y"])
		config["image_feedback_size_x"] = int(config["window_size_x"] / 2)
		config["image_feedback_size_y"] = int(config["window_size_y"] - 100)
		config["fps_in_millisecond"] = int(1000 / config["frames_per_second"])

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
			sys.exit('No Intel F455 camera device detected on the system. Exiting program.')

		return com_port


def main():
	config = _AppConfiguration()
	print(f'preview_mode_enabled: {config.preview_mode_enabled}')


if __name__ == "__main__":
	main()
