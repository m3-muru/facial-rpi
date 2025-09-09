# -*- coding: utf-8 -*-
"""
Created on Mon Mar  7 09:33:51 2022

@author: Maventree
"""
from cv2 import cv2
import mediapipe as mp
import matplotlib.pyplot as plt
import traceback
from src.processor.gesture_detection_status import GestureDetectionStatus
import threading
import traceback
import src.logger.custom_logger as custom_logger
import time
import math
import numpy as np

LOGGER = custom_logger.get_logger()
# Initialize the mediapipe hands class.
mp_hands = mp.solutions.hands

# Set up the Hands functions for images and videos.
hands = mp_hands.Hands(static_image_mode=True, max_num_hands=2, min_detection_confidence=0.5)
hands_videos = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5)

# Initialize the mediapipe drawing class.
mp_drawing = mp.solutions.drawing_utils

window_title = "esc to quit, space to take pic"
active_keypress = 1
global gesture_result

class GestureProcessor(threading.Thread):
	image_feedback_size_x = 400
	image_feedback_size_y = 600

	def __init__(self,gesture_result):
		LOGGER.info("GestureProcessor init...")
		super().__init__()
		LOGGER.info("GestureProcessor init complete.")

	@staticmethod
	def detect_hands_landmarks(image, hands, draw_joints_landmarks_on_image=False):
		'''
		This function performs hands landmarks detection on an image.
		Args:
			image:   The input image with prominent hand(s) whose landmarks needs to be detected.
			hands:   The Hands function required to perform the hands landmarks detection.
			draw_joints_landmarks_on_image:    A boolean value that is if set to true the function draws hands landmarks on the output image.
			should_display_image: A boolean value that is if set to true the function displays the original input image, and the output
					 image with hands landmarks drawn if it was specified and returns nothing.
		Returns:
			drawn_image: A copy of input image with the detected hands landmarks drawn if it was specified.
			results:      The output of the hands landmarks detection on the input image.
		'''
		# Convert the image from BGR into RGB format.
		image_bgr = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

		# Perform the Hands Landmarks Detection.
		results = hands.process(image_bgr)

		image_to_return = None

		

		# If there are joint landmarks detected and we have to draw them
		if results.multi_hand_landmarks and draw_joints_landmarks_on_image:
			# Create a copy of the input image to draw_joints_landmarks_on_image landmarks on.
			drawn_image = image.copy()

			# Iterate over the found hands.
			for hand_landmarks in results.multi_hand_landmarks:
				# Draw the hand landmarks on the copy of the input image.
				mp_drawing.draw_landmarks(
					image=drawn_image, landmark_list=hand_landmarks, connections=mp_hands.HAND_CONNECTIONS,
					landmark_drawing_spec=mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=2),
					connection_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2)
				)

			image_to_return = drawn_image
		# Else, do nothing
		else:
			image_to_return = image

		# # Check if the original input image and the output image are specified to be displayed.
		# if should_display_image:
		#
		#     # Display the original input image and the output image.
		#     plt.figure(figsize=[15, 15])
		#     plt.subplot(121);
		#     plt.imshow(image[:, :, ::-1]);
		#     plt.title("Original Image");
		#     plt.axis('off');
		#     plt.subplot(122);
		#     plt.imshow(drawn_image[:, :, ::-1]);
		#     plt.title("Output");
		#     plt.axis('off');
		#
		# # Otherwise
		# else:
		#
		#     # Return the output image and results of hands landmarks detection.
		#     return drawn_image, results

		return image_to_return, results

	def count_fingers(
				image, results, draw_fingers_counted_on_image=True
		):
			'''
			This function will count the number of fingers up for each hand in the image.
			Args:
				image:   The image of the hands on which the fingers counting is required to be performed.
				results: The output of the hands landmarks detection performed on the image of the hands.
				draw_fingers_counted_on_image:    A boolean value that is if set to true the function writes the total count of fingers of the hands on the
						output image.
				should_display_image: A boolean value that is if set to true the function displays the resultant image and returns nothing.
				multi_hand_detection_enabled: A boolean value that is if set to true multihand use in the event of
										adding more gestures for various purposes.
			Returns:
				output_image:     A copy of the input image with the fingers count written, if it was specified.
				fingers_statuses: A dictionary containing the status (i.e., open or close) of each finger of both hands.
				count:            A dictionary containing the count of the fingers that are up, of both hands.
			'''

			# Get the height and width of the input image.
			height, width, _ = image.shape

			# Initialize a dictionary to store the count of fingers of both hands.
			fingers_counted = {'LEFT': 0, 'RIGHT': 0}

			# Store the indexes of the tips landmarks of each finger of a hand in a list.
			fingers_tips_ids = [mp_hands.HandLandmark.INDEX_FINGER_TIP, mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
								mp_hands.HandLandmark.RING_FINGER_TIP, mp_hands.HandLandmark.PINKY_TIP]

			# Initialize a dictionary to store the status (i.e., True for open and False for close) of each finger of both hands.
			fingers_statuses = {
				'RIGHT_THUMB': False,
				'RIGHT_INDEX': False,
				'RIGHT_MIDDLE': False,
				'RIGHT_RING': False,
				'RIGHT_PINKY': False,
				'LEFT_THUMB': False,
				'LEFT_INDEX': False,
				'LEFT_MIDDLE': False,
				'LEFT_RING': False,
				'LEFT_PINKY': False,
			}

			# Iterate over the found hands in the image.
			for hand_index, hand_info in enumerate(results.multi_handedness):
                
				wrist_results = None
				# Retrieve the label of the found hand.
				# indicates Left,Right or both
				hand_label = hand_info.classification[0].label
				hand_score = hand_info.classification[0].score
				# print(hand_label)

				# Retrieve the landmarks of the found hand.
				# xyz coordinates
				hand_landmarks = results.multi_hand_landmarks[hand_index]
				# print(hand_landmarks)

				if hand_info.classification[0].index == hand_index:

					#text = '{} {}'.format(hand_label, round(hand_score, 2))
					text = '{}'.format(hand_label)
					#extract Coordinates
					coords = tuple(np.multiply(np.array((hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x, hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].y)),[400,600]).astype(int))

					wrist_results = text#, coords
					#print(wrist_results)
					#print(type(wrist_results))
				thumb_joint_list = [[4,3,2]]
				index_joint_list = [[3,2,1]]
				wrist_joint_list = [[1,0,17]]
				"""
				for joint in thumb_joint_list:
					a = np.array([hand_landmarks.landmark[joint[0]].x, hand_landmarks.landmark[joint[0]].y]) # First coord
					b = np.array([hand_landmarks.landmark[joint[1]].x, hand_landmarks.landmark[joint[1]].y]) # Second coord
					c = np.array([hand_landmarks.landmark[joint[2]].x, hand_landmarks.landmark[joint[2]].y]) # Third coord
					
					radians = np.arctan2(c[1] - b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
					angle = np.abs(radians*180.0/np.pi)
					
					if angle > 180.0:
						angle = 360-angle
					
					thumb_angles = str(round(angle, 2))
					position = tuple(np.multiply(b, [640, 480]).astype(int))

					#print(f'Thumb Angle: {thumb_angles}')
				"""
				for joint in index_joint_list:
					a = np.array([hand_landmarks.landmark[joint[0]].x, hand_landmarks.landmark[joint[0]].y]) # First coord
					b = np.array([hand_landmarks.landmark[joint[1]].x, hand_landmarks.landmark[joint[1]].y]) # Second coord
					c = np.array([hand_landmarks.landmark[joint[2]].x, hand_landmarks.landmark[joint[2]].y]) # Third coord
					
					radians = np.arctan2(c[1] - b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
					angle = np.abs(radians*180.0/np.pi)
					
					if angle > 180.0:
						angle = 360-angle
					
					index_angle = str(round(angle, 2))
					position = tuple(np.multiply(b, [640, 480]).astype(int))

					#print(f'Index Finger Angle: {index_angle}')
				
				for joint in wrist_joint_list:
					a = np.array([hand_landmarks.landmark[joint[0]].x, hand_landmarks.landmark[joint[0]].y]) # First coord
					b = np.array([hand_landmarks.landmark[joint[1]].x, hand_landmarks.landmark[joint[1]].y]) # Second coord
					c = np.array([hand_landmarks.landmark[joint[2]].x, hand_landmarks.landmark[joint[2]].y]) # Third coord
					
					radians = np.arctan2(c[1] - b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
					angle = np.abs(radians*180.0/np.pi)
					
					if angle > 180.0:
						angle = 360-angle
					
					wrist_angle = str(round(angle, 2))
					position = tuple(np.multiply(b, [640, 480]).astype(int))

					#print(f'wrist Angle: {wrist_angle}')
				#print(f'Wrist_Index_Finger_Angles: {wrist_angle,index_angle}')
				# Iterate over the indexes of the tips landmarks of each finger of the hand.
				if wrist_results != 'Left': 
					if float(index_angle) < 137:
						LOGGER.gesture("Hand : RIGHT"+", " + f"index_angle: {float(index_angle)}")
						for tip_index in fingers_tips_ids:
							# Retrieve the label (i.e., index, middle, etc.) of the finger on which we are iterating upon.
							finger_name = tip_index.name.split("_")[0]

							# Check if the finger is up by comparing the y-coordinates of the tip and pip landmarks.
							if (hand_landmarks.landmark[tip_index].y < hand_landmarks.landmark[tip_index - 2].y):
								# Update the status of the finger in the dictionary to true.
								fingers_statuses[hand_label.upper() + "_" + finger_name] = True

								# Increment the count of the fingers up of the hand by 1.
								fingers_counted[hand_label.upper()] += 1

						# Retrieve the y-coordinates of the tip and mcp landmarks of the thumb of the hand.
						thumb_tip_x = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].x
						thumb_mcp_x = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP - 2].x

						# Check if the thumb is up by comparing the hand label and the x-coordinates of the retrieved landmarks.
						if (hand_label == 'Right' and (thumb_tip_x < thumb_mcp_x)) or (
								hand_label == 'Left' and (thumb_tip_x > thumb_mcp_x)):
							# Update the status of the thumb in the dictionary to true.
							fingers_statuses[hand_label.upper() + "_THUMB"] = True
							# print(fingers_statuses)

							# Increment the count of the fingers up of the hand by 1.
							fingers_counted[hand_label.upper()] += 1
				
				else:
					if float(index_angle) < 137:
						LOGGER.gesture("Hand : LEFT"+", " + f"index_angle: {float(index_angle)}")
						for tip_index in fingers_tips_ids:

							# Retrieve the label (i.e., index, middle, etc.) of the finger on which we are iterating upon.
							finger_name = tip_index.name.split("_")[0]

							# Check if the finger is up by comparing the y-coordinates of the tip and pip landmarks.
							if (hand_landmarks.landmark[tip_index].y < hand_landmarks.landmark[tip_index - 2].y):
								# Update the status of the finger in the dictionary to true.
								fingers_statuses[hand_label.upper() + "_" + finger_name] = True

								# Increment the count of the fingers up of the hand by 1.
								fingers_counted[hand_label.upper()] += 1

						# Retrieve the y-coordinates of the tip and mcp landmarks of the thumb of the hand.
						thumb_tip_x = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].x
						thumb_mcp_x = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP - 2].x

						# Check if the thumb is up by comparing the hand label and the x-coordinates of the retrieved landmarks.
						if (hand_label == 'Right' and (thumb_tip_x < thumb_mcp_x)) or (
								hand_label == 'Left' and (thumb_tip_x > thumb_mcp_x)):
							# Update the status of the thumb in the dictionary to true.
							fingers_statuses[hand_label.upper() + "_THUMB"] = True
							# print(fingers_statuses)

							# Increment the count of the fingers up of the hand by 1.
							fingers_counted[hand_label.upper()] += 1
					

				#print(f'Total fingers count: {fingers_counted}')

				image_to_return = None

				# # Check if the total count of the fingers of both hands are specified to be written on the output image.
				if draw_fingers_counted_on_image:
					# Create a copy of the input image to write the count of fingers on.
					drawn_image = image.copy()

					# Write the total count of the fingers of both hands on the output image.
					cv2.putText(drawn_image, " Total Fingers: ", (10, 25), cv2.FONT_HERSHEY_COMPLEX, 1, (20, 255, 155), 2)
					cv2.putText(drawn_image, str(sum(fingers_counted.values())), (width // 2 - 150, 240),
								cv2.FONT_HERSHEY_SIMPLEX,
								8.9, (20, 255, 155), 10, 10)

					image_to_return = drawn_image
				else:
					image_to_return = image

				return image_to_return, fingers_statuses, fingers_counted

		#
		# # Check if the output image is specified to be displayed.
		# if should_display_image:
		#
		#     # Display the output image.
		#     plt.figure(figsize=[10, 10])
		#     plt.imshow(output_image[:, :, ::-1]);
		#     plt.title("Output Image");
		#     plt.axis('off');
		#
		# # Otherwise
		# else:
		#
		#     # Return the output image, the status of each finger and the count of the fingers up of both hands.
		#     return output_image, fingers_statuses, count

	def recognize_gestures(image, fingers_statuses, fingers_counted, draw_gesture_recognized_on_image=False):
		'''
		This function will determine the gesture of the left and right hand in the image.
		Args:
			image:            The image of the hands on which the hand gesture recognition is required to be performed.
			fingers_statuses: A dictionary containing the status (i.e., open or close) of each finger of both hands.
			fingers_counted:            A dictionary containing the count of the fingers that are up, of both hands.
			draw_gesture_recognized_on_image:             A boolean value that is if set to true the function writes the gestures of the hands on the
							  output image, after recognition.
			display:          A boolean value that is if set to true the function displays the resultant image and
							  returns nothing.
		Returns:
			output_image:   A copy of the input image with the left and right hand recognized gestures written if it was
							specified.
			hands_gestures: A dictionary containing the recognized gestures of the right and left hand.
		'''

		"""
		# Initialize a dictionary to store the gestures of both hands in the image.
		"""

		gesture_result = None

		# Define the kind of hands we have, naturally its left and right only
		hands_labels = ['LEFT', 'RIGHT']

		image_to_return = None
		target_hand = None
		# Iterate over the results of left and right hand, iteration will happen twice only for both hands starting with the left hand
		for hand_label in hands_labels:

			# Initialize a variable to store the color we will use to write the hands gestures on the image.
			# Initially it is red which represents that the gesture is not recognized.
			color = (255, 255, 0)

			if fingers_counted[hand_label] == 2 and fingers_statuses[hand_label + '_MIDDLE'] and fingers_statuses[hand_label + '_INDEX']:
				target_hand = hand_label
				# Update the gesture value of the hand that we are iterating upon to V SIGN.
				gesture_result = GestureDetectionStatus.VSIGN
				#print(gesture_result)

				# Update the color value to green.
				color = (255, 0, 0)
				break

			if fingers_counted[hand_label] == 1 and fingers_statuses[hand_label + '_INDEX']:
				target_hand = hand_label
				# Update the gesture value of the hand that we are iterating upon to HIGH-FIVE SIGN.
				gesture_result = GestureDetectionStatus.INDEXFINGER
				#print(gesture_result)

				# Update the color value to RED.
				color = (0, 0, 255)
				break

		# Check if the hands gestures are specified to be written.
		if draw_gesture_recognized_on_image and target_hand:
			# Create a copy of the input image.
			drawn_image = image.copy()

			# Write the hand gesture on the output image.
			cv2.putText(
				drawn_image,
				target_hand + ': ' + gesture_result.name,
				(10, 5 * 60),
				cv2.FONT_HERSHEY_PLAIN, 2, color, 5
			)

			image_to_return = drawn_image
		else:
			image_to_return = image

		return image_to_return, gesture_result

	def detect_gesture(
			image=None, multi_hand_detection_enabled=False, maximum_hands_in_frame_threshold=2,
			draw_joints_landmarks_on_image=False,
			draw_fingers_counted_on_image=False,
			draw_gesture_recognized_on_image=False
	):
		final_result = {
			"image": None,
			"gesture": None
		}

		# Read a sample image and perform the hand gesture recognition on it after flipping it horizontally.
		if image is None:
			image = cv2.imread('./image/image_1.jpg')  # Image feed from F455 goes through here.

		flipped_image = cv2.flip(image, 1)

		# Ensure there's a usable frame after flipping
		if image is not None:
			image, results = GestureProcessor.detect_hands_landmarks(
				flipped_image, hands,
				draw_joints_landmarks_on_image
			)

			# If no hands detected
			if not results.multi_handedness:
				# Pass back the image to be displayed so the stream looks "live"
				final_result['image'] = image
				return final_result

			# If we have to check for multiple hands
			if multi_hand_detection_enabled:
				# If the amount of required hands in frame is not within the threshold
				if len(results.multi_handedness) != maximum_hands_in_frame_threshold:
					# Pass back the image to be displayed so the stream looks "live"
					final_result['image'] = image
					return final_result
			# Else just be concern with 1 hand
			else:
				# If the amount of required hands in frame does not have at least 1 hand
				if len(results.multi_handedness) != 1:
					# Pass back the image to be displayed so the stream looks "live"
					final_result['image'] = image
					return final_result

			image, fingers_statuses, fingers_counted = GestureProcessor.count_fingers(
				image, results,
				draw_fingers_counted_on_image
			)

			image, gesture = GestureProcessor.recognize_gestures(
				image,
				fingers_statuses,
				fingers_counted,
				draw_gesture_recognized_on_image
			)

			# Pass back the image to be displayed so the stream looks "live"
			final_result['image'] = image
			final_result['gesture'] = gesture
			return final_result
		else:
			print('Image NONE!')

	def display_image(image):
		global active_keypress

		image = cv2.resize(image, (GestureProcessor.image_feedback_size_x, GestureProcessor.image_feedback_size_y))
		cv2.imshow(window_title, image)
		active_keypress = cv2.waitKey(1)


def start_camera(camera_number):
	global active_keypress, window_title

	# https://stackoverflow.com/a/34588758/11537143
	cv2.namedWindow(window_title)

	cam = cv2.VideoCapture(camera_number)
	img_counter = 0
	iteration_counter = 0

	while True:
		iteration_counter = iteration_counter + 1
		has_image, image = cam.read()

		# Save original image - Gesture processor requires original image(? TBC)
		image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)

		if not has_image:
			print("failed to grab image")
			break

		if iteration_counter % 1 == 0:
			iteration_counter = 0
			try:
				result = GestureProcessor.detect_gesture(
					image, multi_hand_detection_enabled=False, maximum_hands_in_frame_threshold=2,
					draw_joints_landmarks_on_image=True,
					draw_fingers_counted_on_image=True,
					draw_gesture_recognized_on_image=True
				)
				# print(result)
				GestureProcessor.display_image(result['image'])
			except TypeError as e:
				print(traceback.format_exc())
				print(f'@@@@@Error see here: {e}')
				pass

		if active_keypress % 256 == 27:
			# ESC pressed
			print("Escape hit, closing...")
			break
		elif active_keypress % 256 == 32:
			# SPACE pressed
			img_name = "./image/image_test_{}.png".format(img_counter)
			cv2.imwrite(img_name, image)
			print("{} written!".format(img_name))
			img_counter += 1

	cam.release()
	cv2.destroyAllWindows()


def main():
	start_camera(1)
	# detect_gesture()

	print('Program ended..')


if __name__ == '__main__':
	main()
