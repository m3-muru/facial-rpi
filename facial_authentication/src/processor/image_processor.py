import os
import sys
import threading
import traceback
import time
import json
from PIL import Image, ImageTk
import numpy as np
import rsid_py
from datetime import datetime

import src.utility.gui_feedback_color_utility as color_utility
import src.logger.custom_logger as custom_logger
from src.processor.face_detection_processor import FaceDetectionProcessor
from src.processor.face_processor import FaceProcessor
from src.processor.face_detection_status import FaceDetectionStatus

LOGGER = custom_logger.get_logger()

try :
    import numpy as np
except ImportError:
    print('Failed importing numpy. Please install it (pip install numpy).')
    exit(0)

try:
    import cv2
except ImportError:
    print('Failed importing cv2. Please install it (pip install opencv-python).')
    exit(0)


class ImageProcessor(threading.Thread):
    def __init__(self, feedback_livestream_image_q, feedback_livestream_detections_q, config):
        LOGGER.info("ImageProcessor init...")
        super().__init__()

        # Retrieve config
        self.config = config
        self.feedback_livestream_image_q = feedback_livestream_image_q

        # Initialized required communication queues
        self.feedback_livestream_detections_q = feedback_livestream_detections_q

        # Initialized required properties
        self.livestream_detections = []  # Initializing

        # TODO: [debugger], set to True to printout live image properties parsed by the camera
        self.debug_printout_preview_image_properties = False
        # TODO: [debugger] set to True to preview live images parse by the camera
        self.debug_preview_camera_image_enabled = False
        # TODO: [debugger], set to True to save live images parsed by the camera, can be used for debugging real time image.training gesture recognition (in the future) if required
        self.debug_save_previewed_image = False

        #stores gesture results
        self.feedback_gesture = None

        # Start timestamp
        self.start_time = datetime.now()

        LOGGER.info("ImageProcessor init complete.")

    def run(self):
        LOGGER.info("ImageProcessor started.")
        # Initialize and start status msg and faces detected updater
        self.poll_feedback_livestream_detections_q()

        preview_cfg = rsid_py.PreviewConfig()
        preview_cfg.camera_number = -1  # -1 means auto detect
        preview = rsid_py.Preview(preview_cfg)
        preview.start(self.on_image_available)
        while True:
            time.sleep(1)

    def poll_feedback_livestream_detections_q(self):
        def _poll_feedback_livestream_detections_q():
            nonlocal self
            while True:
                self.livestream_detections = self.feedback_livestream_detections_q.get()  # Retrieving from queue
                
                LOGGER.info(f'livestream_detections(face coordinates) updated')
                LOGGER.info(f'********************************************************************************************Total face detection boxes to draw in image: {len(self.livestream_detections)}')
                
        threading.Thread(target=_poll_feedback_livestream_detections_q, daemon=True).start()

    # Draw detection box around faces detected in the livestream onto the RGB image
    # NOTE: The drawing of the detection box occurring will only happen
    #   AFTER enrolment or authentication is triggered in face_processor.
    #   In normal circumstances, there will not be any detected faces, so nothing will be drawn
    @staticmethod
    def draw_detection_box_on_image(detection, image):
        face = detection.get('face')
        status = detection.get("status")

        scale_x = image.shape[1] / 1080.0
        scale_y = image.shape[0] / 1920.0
        x = int(face.x * scale_x)
        y = int(face.y * scale_y)
        w = int(face.w * scale_y)
        h = int(face.h * scale_y)

        start_point = (x, y)
        end_point = (x + w, y + h)

        # Get the color for the detection box
        color = color_utility.get_detection_border_feedback_color(status)

        # Create a semi-transparent overlay
        overlay = image.copy()
        alpha = 0.3

        # Draw a filled rectangle with rounded corners
        radius = int(min(w, h) * 0.15)
        cv2.rectangle(overlay, start_point, end_point, color, thickness=cv2.FILLED)
        cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0, image)

        # Draw the border with rounded corners
        thickness = max(3, int(min(w, h) * 0.015))
        cv2.rectangle(image, start_point, end_point, color, thickness)

        # Status text mapping
        status_text_map = {
            FaceDetectionStatus.PENDING: "PROCESSING",
            FaceDetectionStatus.REJECTED: "REJECTED",
            FaceDetectionStatus.ACCEPTED: "ACCEPTED"
        }
        text = status_text_map.get(status, "UNKNOWN")

        # Set font color based on text
        if text == "PROCESSING":
            text_color = (0, 0, 0)  # Black text
        else:
            text_color = (255, 255, 255)  # White text

        # Calculate dynamic font scale
        font_scale = min(w, h) / 200.0
        font_thickness = max(2, int(font_scale * 2))
        font = cv2.FONT_HERSHEY_SIMPLEX

        # Calculate text size and position
        (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, font_thickness)
        text_x = x + (w - text_width) // 2
        text_y = y - int(text_height * 1.2)

        # Ensure text is not drawn off the top edge of the image
        if text_y - text_height < 0:
            text_y = y + h + int(text_height * 1.2)

        # Draw a background rectangle for the text with the detection box color
        bg_color = color  # Use the detection box color for the background
        bg_padding = int(text_height * 0.3)  # Padding around the text
        top_left = (text_x - bg_padding, text_y - text_height - bg_padding)
        bottom_right = (text_x + text_width + bg_padding, text_y + bg_padding)
        cv2.rectangle(image, top_left, bottom_right, bg_color, cv2.FILLED)

        # Draw the text
        cv2.putText(image, text, (text_x, text_y), font, font_scale, text_color, font_thickness, cv2.LINE_AA)

        # Calculate the text region and ensure it's within bounds
        text_region_y1 = max(text_y - text_height - bg_padding, 0)
        text_region_y2 = min(text_y + bg_padding, image.shape[0])
        text_region_x1 = max(text_x - bg_padding, 0)
        text_region_x2 = min(text_x + text_width + bg_padding, image.shape[1])

        text_region = image[text_region_y1:text_region_y2, text_region_x1:text_region_x2]

        # Check if the text region is valid before flipping
        if text_region is not None and text_region.size > 0:
            flipped_text_region = cv2.flip(text_region, 1)
            image[text_region_y1:text_region_y2, text_region_x1:text_region_x2] = flipped_text_region

        return image

    def create_tk_image_safely(self, cv2_image):
        """
        Thread-safe method to create Tkinter PhotoImage
        Put the PIL Image in the queue instead of PhotoImage, let the GUI thread handle PhotoImage creation
        """
        try:
            # Convert CV2 image to PIL Image
            livestream_image = Image.fromarray(cv2_image)
            livestream_image = livestream_image.resize((self.config.image_feedback_size_x, self.config.image_feedback_size_y))
            
            # Put the PIL Image directly in the queue - let the GUI handle PhotoImage creation
            self.feedback_livestream_image_q.put(livestream_image)
                
        except Exception as e:
            LOGGER.error(f"Error in create_tk_image_safely: {e}")

    def on_image_available(self, image):
        try:
            # Operations to prepare RGB image
            buffer = memoryview(image.get_buffer())
            arr = np.asarray(buffer, dtype=np.uint8)
            array2d = arr.reshape((image.height, image.width, -1))

            if self.livestream_detections:
                # Draw detection box around faces detected in the livestream onto the RGB image
                # NOTE: The drawing of the detection box occurring will only happen
                #   AFTER enrolment or authentication is triggered in face_processor.
                #   In normal circumstances, there will not be any detected faces, so nothing will be drawn
                for detection in self.livestream_detections:   # Processing
                    ImageProcessor.draw_detection_box_on_image(detection, array2d)

            fd_compatible_image = array2d
            fd_compatible_image = cv2.cvtColor(fd_compatible_image, cv2.COLOR_BGR2RGB)

            self.feedback_fd = FaceDetectionProcessor.detect_face(fd_compatible_image)

            if self.feedback_fd['face_detected'] is not None:
                f = open('./write/feed_fd_temp.txt', 'w')
                f.write(str(self.feedback_fd['face_detected']))
                f.close()
            else:
                f = open('./write/feed_fd_temp.txt', 'w')
                f.write(str(self.feedback_fd['face_detected']))
                f.close()

            cv2_image = cv2.flip(array2d, 1)

            # Use thread-safe method to create Tkinter PhotoImage
            self.create_tk_image_safely(cv2_image)

            if self.debug_printout_preview_image_properties:
                ImageProcessor.print_image_properties(cv2_image)

            if self.debug_preview_camera_image_enabled:
                ImageProcessor.preview_camera_image(cv2_image)

            if self.debug_save_previewed_image:
                if hasattr(self, 'debug_save_previewed_image_config_init') is False:
                    # TODO: [debugger] increase value to save more image, set to 0 for infinite
                    self.debug_total_image_to_save = 10
                    self.debug_saved_image_counter = 0
                    self.debug_save_previewed_image_config_init = True

                ImageProcessor.save_image(cv2_image, self.debug_saved_image_counter + 1)
                self.debug_saved_image_counter += 1
                if self.debug_saved_image_counter == self.debug_total_image_to_save:
                    self.debug_save_previewed_image = False

        except Exception as e:
            LOGGER.critical(f"Exception in on_image_available: {e}")
            LOGGER.critical(f"-" * 60)
            LOGGER.critical(traceback.format_exc())
            LOGGER.critical(f"-" * 60)

    @staticmethod
    def preview_camera_image(cv2_image):
        window_name = "Camera Image Previewer"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, (int(720 / 1.6), int(1280 / 1.6)))
        cv2.imshow(window_name, cv2_image)
        cv2.waitKey(1)

    @staticmethod
    def save_image(cv2_image, image_counter=''):
        height, width, channels = cv2_image.shape
        cv2.imwrite(f'image-{image_counter}-{width}x{height}.jpg', cv2_image)

    @staticmethod
    def print_image_properties(cv2_image):
        height, width, channels = cv2_image.shape
        custom_logger.get_logger().debug(f'on_image_available()! {width}x{height}, c={channels}')