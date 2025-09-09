from win32api import GetMonitorInfo, MonitorFromPoint
import src.logger.custom_logger as custom_logger

LOGGER = custom_logger.get_logger()
ALIGN_CENTER = 1
ALIGN_BOTTOM_RIGHT = 2
ALIGN_TOP_RIGHT = 3
VALID_ALIGNMENT = {
	ALIGN_CENTER,
	ALIGN_BOTTOM_RIGHT,
	ALIGN_TOP_RIGHT
}


def get_gui_window_properties(target_window):
	monitor_info = GetMonitorInfo(MonitorFromPoint((0, 0)))
	monitor_area = monitor_info.get("Monitor")
	work_area = monitor_info.get("Work")

	target_window.update_idletasks()
	screen_width = target_window.winfo_screenwidth()
	screen_height = target_window.winfo_screenheight()
	work_area_x = work_area[2]
	work_area_y = work_area[3]

	width = target_window.winfo_width()
	frm_width = target_window.winfo_rootx() - target_window.winfo_x()
	height = target_window.winfo_height()
	title_bar_height = target_window.winfo_rooty() - target_window.winfo_y()

	win_width = width + 2 * frm_width
	win_height = height + title_bar_height + frm_width
	centered_x_pos = target_window.winfo_screenwidth() // 2 - win_width // 2
	centered_y_pos = target_window.winfo_screenheight() // 2 - win_height // 2

	total_app_height_occupied = height + title_bar_height
	total_app_width_occupied = width + frm_width

	taskbar_height = monitor_area[3] - work_area_y
	total_taskbar_and_app_height_occupied = total_app_height_occupied + taskbar_height

	remaining_free_screen_width_available = work_area_x - total_app_width_occupied
	remaining_free_screen_height_available = screen_height - total_taskbar_and_app_height_occupied

	window_properties = {
		'monitor_info': monitor_info,
		'monitor_area': monitor_area,
		'work_area': work_area,
		'screen_width': screen_width,
		'screen_height': screen_height,
		'work_area_x': work_area_x,
		'work_area_y': work_area_y,
		'width': width,
		'frm_width': frm_width,
		'win_width': win_width,
		'height': height,
		'title_bar_height': title_bar_height,
		'win_height': win_height,
		'centered_x_pos': centered_x_pos,
		'centered_y_pos': centered_y_pos,
		'total_app_height_occupied': total_app_height_occupied,
		'total_app_width_occupied': total_app_width_occupied,
		'taskbar_height': taskbar_height,
		'total_taskbar_and_app_height_occupied': total_taskbar_and_app_height_occupied,
		'remaining_free_screen_width_available': remaining_free_screen_width_available,
		'remaining_free_screen_height_available': remaining_free_screen_height_available,
		'top_right_x_pos': work_area_x - win_width,  # Top right X position
		'top_right_y_pos': 0,  # Top right Y position (0 for top)
	}
	return window_properties


def align_window(target_window, target_align_position=ALIGN_CENTER):
	if target_align_position not in VALID_ALIGNMENT:
		error_msg = "Unknown target_align_position provided"
		LOGGER.error(error_msg)
		raise ValueError(error_msg)

	window_properties = get_gui_window_properties(target_window)
	if target_align_position == ALIGN_CENTER:
		target_window.geometry(
			'+{}+{}'.format(
				window_properties.get('centered_x_pos'),
				window_properties.get('centered_y_pos')
			)
		)
	elif target_align_position == ALIGN_BOTTOM_RIGHT:
		target_window.geometry(
			'+{}+{}'.format(
				window_properties.get('remaining_free_screen_width_available'),
				window_properties.get('remaining_free_screen_height_available')
			)
		)
	elif target_align_position == ALIGN_TOP_RIGHT:  # New condition for top right alignment
		target_window.geometry(
			'+{}+{}'.format(
				window_properties.get('top_right_x_pos'),
				window_properties.get('top_right_y_pos')
			)
		)

	target_window.deiconify()


def print_window_properties(target_window):
	window_properties = get_gui_window_properties(target_window)

	LOGGER.debug('')
	LOGGER.debug('--------------------WINDOW PROPERTIES--------------------')
	for key, value in window_properties.items():
		LOGGER.debug(f'{key}: {value}')
