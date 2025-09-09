import logging
from datetime import datetime
from pathlib import Path
from src.logger.custom_log_filter import CustomLogFilter
from src.logger.custom_log_formatter import CustomLogFormatter

# TODO: https://stackoverflow.com/a/39351132/11537143
current_date = datetime.today().strftime('%Y-%m-%d')

# https://stackoverflow.com/a/53465812/11537143
# In the future, if multiple module uses the method below to retrieve root dir,
# then we should the method into a definition class
PROJECT_ROOT_DIR = str(Path(__file__).parent.parent.parent)
LOG_FOLDER_DIR = PROJECT_ROOT_DIR + "\\log"
Path(LOG_FOLDER_DIR).mkdir(parents=True, exist_ok=True)

# https://stackoverflow.com/a/13733863/11537143
# https://stackoverflow.com/a/8163115/11537143
logger = logging.getLogger('custom_logger')
log_formatter = logging.Formatter(
	'[%(asctime)s] [%(threadName)-10.10s] [%(filename)-18.18s:%(lineno)-4.4d] [%(levelname)-8.8s]  %(message)s')
logger.setLevel(logging.DEBUG)

# Defaults output to stderr, initialize with stdout to output white text instead
console_handler = logging.StreamHandler()
console_log_formatter = CustomLogFormatter()
console_handler.setFormatter(console_log_formatter)
logger.addHandler(console_handler)

info_handler = logging.FileHandler(f'{LOG_FOLDER_DIR}/{current_date}-info.log')
info_handler.setFormatter(log_formatter)
info_handler.setLevel(logging.INFO)
info_handler.addFilter(CustomLogFilter(logging.INFO))
logger.addHandler(info_handler)
debug_handler = logging.FileHandler(f'{LOG_FOLDER_DIR}/{current_date}-info.log')
debug_handler.setFormatter(log_formatter)
debug_handler.setLevel(logging.DEBUG)
debug_handler.addFilter(CustomLogFilter(logging.DEBUG))
logger.addHandler(debug_handler)
facerec_handler = logging.FileHandler(f'{LOG_FOLDER_DIR}/{current_date}-info.log')
facerec_handler.setFormatter(log_formatter)
facerec_handler.setLevel(123)
facerec_handler.addFilter(CustomLogFilter(123))
logger.addHandler(facerec_handler)

gesture_handler = logging.FileHandler(f'{LOG_FOLDER_DIR}/{current_date}-info.log')
gesture_handler.setFormatter(log_formatter)
gesture_handler.setLevel(456)
gesture_handler.addFilter(CustomLogFilter(456))
logger.addHandler(gesture_handler)

warning_handler = logging.FileHandler(f'{LOG_FOLDER_DIR}/{current_date}-issues.log')
warning_handler.setFormatter(log_formatter)
warning_handler.setLevel(logging.WARNING)
warning_handler.addFilter(CustomLogFilter(logging.WARNING))
logger.addHandler(warning_handler)
error_handler = logging.FileHandler(f'{LOG_FOLDER_DIR}/{current_date}-issues.log')
error_handler.setFormatter(log_formatter)
error_handler.setLevel(logging.ERROR)
error_handler.addFilter(CustomLogFilter(logging.ERROR))
logger.addHandler(error_handler)
critical_handler = logging.FileHandler(f'{LOG_FOLDER_DIR}/{current_date}-issues.log')
critical_handler.setFormatter(log_formatter)
critical_handler.setLevel(logging.CRITICAL)
critical_handler.addFilter(CustomLogFilter(logging.CRITICAL))
logger.addHandler(critical_handler)

full_handler = logging.FileHandler(f'{LOG_FOLDER_DIR}/{current_date}-full.log')
full_handler.setFormatter(log_formatter)
full_handler.setLevel(logging.DEBUG)
logger.addHandler(full_handler)


# https://stackoverflow.com/a/35804945/11537143
def add_logging_level(level_name, level_num, method_name=None):
	"""
	Comprehensively adds a new logging level to the `logging` module and the
	currently configured logging class.

	`levelName` becomes an attribute of the `logging` module with the value
	`levelNum`. `methodName` becomes a convenience method for both `logging`
	itself and the class returned by `logging.getLoggerClass()` (usually just
	`logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
	used.

	To avoid accidental clobberings of existing attributes, this method will
	raise an `AttributeError` if the level name is already an attribute of the
	`logging` module or if the method name is already present
	"""
	if not method_name:
		method_name = level_name.lower()

	if hasattr(logging, level_name):
		raise AttributeError('{} already defined in logging module'.format(level_name))
	if hasattr(logging, method_name):
		raise AttributeError('{} already defined in logging module'.format(method_name))
	if hasattr(logging.getLoggerClass(), method_name):
		raise AttributeError('{} already defined in logger class'.format(method_name))

	# This method was inspired by the answers to Stack Overflow post
	# http://stackoverflow.com/q/2183233/2988730, especially
	# http://stackoverflow.com/a/13638084/2988730
	def log_for_level(self, message, *args, **kwargs):
		if self.isEnabledFor(level_num):
			self._log(level_num, message, args, **kwargs)

	def log_to_root(message, *args, **kwargs):
		logging.log(level_num, message, *args, **kwargs)

	logging.addLevelName(level_num, level_name)
	setattr(logging, level_name, level_num)
	setattr(logging.getLoggerClass(), method_name, log_for_level)
	setattr(logging, method_name, log_to_root)


add_logging_level('FACE_REC', 123)
add_logging_level('GESTURE', 456)


def get_logger():
	return logger


def main():
	get_logger().debug("debug test log")
	get_logger().info("info test log")
	get_logger().face_rec("facerec test log")
	get_logger().gesture("gesture test log")
	get_logger().warning("warning test log")
	get_logger().error("error test log")
	get_logger().critical("critical test log")


if __name__ == "__main__":
	main()
