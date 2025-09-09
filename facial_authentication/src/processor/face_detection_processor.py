# -*- coding: utf-8 -*-
"""
Created on Mon Mar  7 09:33:51 2022

@author: Maventree
"""
from cv2 import cv2
import mediapipe as mp
import traceback
import threading
import src.logger.custom_logger as custom_logger
import time

LOGGER = custom_logger.get_logger()

# Initialize the mediapipe face detection class.
mp_face_detection = mp.solutions.face_detection

# Set up the Face Detection functions for images and videos.
face_detection = mp_face_detection.FaceDetection(min_detection_confidence=0.5)

# Initialize the mediapipe drawing class.
mp_drawing = mp.solutions.drawing_utils

window_title = "esc to quit, space to take pic"
active_keypress = 1


class FaceDetectionProcessor(threading.Thread):
    image_feedback_size_x = 400
    image_feedback_size_y = 600

    def __init__(self):
        LOGGER.info("FaceDetectionProcessor init...")
        super().__init__()
        LOGGER.info("FaceDetectionProcessor init complete.")

    @staticmethod
    def detect_faces(image, face_detection, draw_face_landmarks_on_image=False):
        '''
        This function performs face detection on an image.
        Args:
            image:   The input image with prominent face(s) whose landmarks need to be detected.
            face_detection:   The FaceDetection function required to perform the face landmarks detection.
            draw_face_landmarks_on_image:    A boolean value that is if set to true the function draws face landmarks on the output image.
        Returns:
            image_to_return: A copy of input image with the detected face landmarks drawn if specified.
            results: The output of the face landmarks detection on the input image.
        '''
        # Convert the image from BGR into RGB format.
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Perform the Face Detection.
        results = face_detection.process(image_rgb)

        image_to_return = image

        # If face landmarks are detected and we have to draw them
        if results.detections and draw_face_landmarks_on_image:
            # Create a copy of the input image to draw landmarks on.
            drawn_image = image.copy()

            # Iterate over the found faces.
            for detection in results.detections:
                # Draw the face landmarks on the copy of the input image.
                mp_drawing.draw_detection(drawn_image, detection)

            image_to_return = drawn_image

        return image_to_return, results

    def detect_face(
            image=None, draw_face_landmarks_on_image=False
    ):
        final_result = {
            "image": None,
            "face_detected": False
        }

        # Read a sample image if no image is provided.
        if image is None:
            image = cv2.imread('./image/image_1.jpg')  # Replace with your image path.

        flipped_image = cv2.flip(image, 1)

        # Ensure there's a usable frame after flipping
        if flipped_image is not None:
            image, results = FaceDetectionProcessor.detect_faces(
                flipped_image, face_detection,
                draw_face_landmarks_on_image
            )

            # If no faces detected
            if not results.detections:
                # Pass back the image to be displayed so the stream looks "live"
                final_result['image'] = image
                return final_result

            # If faces detected
            final_result['image'] = image
            final_result['face_detected'] = True
            return final_result
        else:
            print('Image NONE!')

    def display_image(image):
        global active_keypress

        image = cv2.resize(image, (FaceDetectionProcessor.image_feedback_size_x, FaceDetectionProcessor.image_feedback_size_y))
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

        # Rotate the image if needed (like in the original code).
        image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)

        if not has_image:
            print("Failed to grab image")
            break

        if iteration_counter % 1 == 0:
            iteration_counter = 0
            try:
                result = FaceDetectionProcessor.detect_face(
                    image, draw_face_landmarks_on_image=True
                )
                FaceDetectionProcessor.display_image(result['image'])
            except TypeError as e:
                print(traceback.format_exc())
                print(f'Error: {e}')
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
    print('Program ended..')


if __name__ == '__main__':
    main()
