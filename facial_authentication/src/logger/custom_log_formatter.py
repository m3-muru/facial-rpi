import logging

# https://stackoverflow.com/a/56944256/11537143
class CustomLogFormatter(logging.Formatter):
	pink = "\x1b[35;1m"
	teal = "\x1b[1;36m"
	blue = "\x1b[34m"
	yellow = "\x1b[1;33m"
	red = "\x1b[31;20m"
	bold_red = "\x1b[31;1m"
	reset = "\x1b[0m"
	format = '[%(asctime)s] [%(threadName)-10.10s] [%(filename)-18.18s:%(lineno)-4.4d] [%(levelname)-8.8s]  %(message)s'

	FORMATS = {
		logging.DEBUG: pink + format + reset,
		logging.INFO: teal + format + reset,
		123: blue + format + reset,
		456: blue + format + reset,
		logging.WARNING: yellow + format + reset,
		logging.ERROR: red + format + reset,
		logging.CRITICAL: bold_red + format + reset,
	}

	def format(self, record):
		log_fmt = self.FORMATS.get(record.levelno)
		formatter = logging.Formatter(log_fmt)
		return formatter.format(record)
