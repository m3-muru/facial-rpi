class FaceDetectionMessage:
	enroll_custom_msg = {
		"EnrollStatus.Success": "Enrollment successful",
		"EnrollStatus.NoFaceDetected": "No Face Detected",
		"EnrollStatus.FaceDetected": "Face Detected",
		"EnrollStatus.LedFlowSuccess": "Led Flow Success",
		"EnrollStatus.FaceIsTooFarToTheTop": "Face Is Too Far To The Top",
		"EnrollStatus.FaceIsTooFarToTheBottom": "Face Is Too Far To The Bottom",
		"EnrollStatus.FaceIsTooFarToTheRight": "Face Is Too Far To The Right",
		"EnrollStatus.FaceIsTooFarToTheLeft": "Face Is Too Far To The Left",
		"EnrollStatus.FaceTiltIsTooUp": "Face Tilt Is Too Up",
		"EnrollStatus.FaceTiltIsTooDown": "Face Tilt Is Too Down",
		"EnrollStatus.FaceTiltIsTooRight": "Face Tilt Is Too Right",
		"EnrollStatus.FaceTiltIsTooLeft": "Face Tilt Is Too Left",
		"EnrollStatus.FaceIsNotFrontal": "Face Is Not Frontal",
		"EnrollStatus.CameraStarted": "Camera Started",
		"EnrollStatus.CameraStopped": "Camera Stopped",
		"EnrollStatus.MultipleFacesDetected": "Multiple Faces Detected",
		"EnrollStatus.Failure": "Enrollment Failure",
		"EnrollStatus.DeviceError": "Device Error",
		"EnrollStatus.EnrollWithMaskIsForbidden": "Enroll With Mask Is Forbidden",
		"EnrollStatus.Spoof": "Spoof Detected",
		"EnrollStatus.SerialOk": "Serial Ok",
		"EnrollStatus.SerialError": "Serial Error",
		"EnrollStatus.SerialSecurityError": "Serial Security Error",
		"EnrollStatus.VersionMismatch": "Version Mismatch",
		"EnrollStatus.CrcError": "Crc Error",
		"EnrollStatus.Reserved1": "Reserved 1",
		"EnrollStatus.Reserved2": "Reserved 2",
		"EnrollStatus.Reserved3": "Reserved 3",
	}

	auth_custom_msg = {
		"AuthenticateStatus.Success": "Authentication successful",
		"AuthenticateStatus.NoFaceDetected": "No Face Detected",
		"AuthenticateStatus.FaceDetected": "Face Detected",
		"AuthenticateStatus.LedFlowSuccess": "Led Flow Success",
		"AuthenticateStatus.FaceIsTooFarToTheTop": "Face Is Too Far To The Top",
		"AuthenticateStatus.FaceIsTooFarToTheBottom": "Face Is Too Far To The Bottom",
		"AuthenticateStatus.FaceIsTooFarToTheRight": "Face Is Too Far To The Right",
		"AuthenticateStatus.FaceIsTooFarToTheLeft": "Face Is Too Far To The Left",
		"AuthenticateStatus.FaceTiltIsTooUp": "Face Tilt Is Too Up",
		"AuthenticateStatus.FaceTiltIsTooDown": "Face Tilt Is Too Down",
		"AuthenticateStatus.FaceTiltIsTooRight": "Face Tilt Is Too Right",
		"AuthenticateStatus.FaceTiltIsTooLeft": "Face Tilt Is Too Left",
		"AuthenticateStatus.CameraStarted": "Camera Started",
		"AuthenticateStatus.CameraStopped": "Camera Stopped",
		"AuthenticateStatus.MaskDetectedInHighSecurity": "Mask Detected In High Security",
		"AuthenticateStatus.Spoof": "Spoof Detected",
		"AuthenticateStatus.Forbidden": "Forbidden",
		"AuthenticateStatus.DeviceError": "Device Error",
		"AuthenticateStatus.Failure": "Failure",
		"AuthenticateStatus.SerialOk": "Serial Ok",
		"AuthenticateStatus.SerialError": "Serial Error",
		"AuthenticateStatus.SerialSecurityError": "Serial Security Error",
		"AuthenticateStatus.VersionMismatch": "Version Mismatch",
		"AuthenticateStatus.CrcError": "Crc Error",
		"AuthenticateStatus.Reserved1": "Reserved 1",
		"AuthenticateStatus.Reserved2": "Reserved 2",
		"AuthenticateStatus.Reserved3": "Reserved 3",
	}

	@staticmethod
	def cleanup_enroll_msg(msg):
		# Access the value of the enum to get the dictionary, then iterate through the key value pair
		# Reference: https://stackoverflow.com/a/24487545/11537143
		for key, value in FaceDetectionMessage.enroll_custom_msg.items():
			if key in msg:
				msg = msg.replace(key, value)
				break
		return msg

	@staticmethod
	def cleanup_auth_msg(msg):
		# Access the value of the enum to get the dictionary, then iterate through the key value pair
		# Reference: https://stackoverflow.com/a/24487545/11537143
		for key, value in FaceDetectionMessage.auth_custom_msg.items():
			if key in msg:
				msg = msg.replace(key, value)
				break
		return msg

	@staticmethod
	def cleanup_msg(msg):
		if "EnrollStatus." in msg:
			msg = FaceDetectionMessage.cleanup_enroll_msg(msg)
		elif "AuthenticateStatus" in msg:
			msg = FaceDetectionMessage.cleanup_auth_msg(msg)

		return msg
