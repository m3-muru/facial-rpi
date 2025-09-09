from src.processor.face_detection_status import FaceDetectionStatus


def get_detection_border_feedback_color(status):
	return {
		FaceDetectionStatus.PENDING: (204, 204, 51),  # Yellow
		FaceDetectionStatus.REJECTED: (204, 17, 17),  # Red
		FaceDetectionStatus.ACCEPTED: (22, 108, 17)  # Green
	}.get(status, (204, 51, 165))  # Default unknown - Purple


def get_status_bar_feedback_color(status):
	return {
		FaceDetectionStatus.PENDING: "#cccc33",  # Yellow
		FaceDetectionStatus.REJECTED: "#cc1111",  # Red
		FaceDetectionStatus.ACCEPTED: "#166c11"  # Green
	}.get(status, "#000000")  # Default unknown - Black
