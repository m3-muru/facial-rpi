import os
import sys
import threading
import traceback
import time
import json
from PIL import Image, ImageTk

import rsid_py

import src.utility.gui_feedback_color_utility as color_utility
import src.logger.custom_logger as custom_logger
from src.processor.gesture_processor import GestureProcessor
from src.processor.gesture_detection_status import GestureDetectionStatus
from src.processor.face_processor import FaceProcessor

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
        self.buffer_array = []
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
                LOGGER.info(f'Total face detection boxes to draw in image: {len(self.livestream_detections)}')
        threading.Thread(target=_poll_feedback_livestream_detections_q, daemon=True).start()

    # Draw detection box around faces detected in the livestream onto the RGB image
    # NOTE: The drawing of the detection box occurring will only happen
    #   AFTER enrolment or authentication is triggered in face_processor.
    #   In normal circumstances, there will not be any detected faces, so nothing will be drawn
    @staticmethod
    def draw_detection_box_on_image(detection, image):
        # scale rets from 1080p
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

        # Detection border colors
        # in progress = yellow, success = green, failure = red
        color = color_utility.get_detection_border_feedback_color(status)

        thickness = 2
        cv2.rectangle(image, start_point, end_point, color, thickness)

    def on_image_available(self, image):
        try:
            # Operations to prepare RGB image
            buffer = memoryview(image.get_buffer())
            arr = np.asarray(buffer, dtype=np.uint8)
            array2d = arr.reshape((image.height, image.width, -1))

            #if self.livestream_detections:
                # Draw detection box around faces detected in the livestream onto the RGB image
                # NOTE: The drawing of the detection box occurring will only happen
                #   AFTER enrolment or authentication is triggered in face_processor.
                #   In normal circumstances, there will not be any detected faces, so nothing will be drawn
                #for detection in self.livestream_detections:   # Processing
                    #ImageProcessor.draw_detection_box_on_image(detection, array2d)

            gesture_compatible_image = array2d
            gesture_compatible_image = cv2.cvtColor(gesture_compatible_image, cv2.COLOR_BGR2RGB)
            '''
            self.feedback_gesture = GestureProcessor.detect_gesture(
                gesture_compatible_image,
                draw_joints_landmarks_on_image=True,
                draw_fingers_counted_on_image=True,
                draw_gesture_recognized_on_image=True
            )
            '''
            temp_results = GestureProcessor.detect_gesture(
                gesture_compatible_image,
                draw_joints_landmarks_on_image=True,
                draw_fingers_counted_on_image=True,
                draw_gesture_recognized_on_image=True
            )
            
            
            if temp_results['gesture'] is not None:
                if str(temp_results['gesture'].value) == '1':
                    self.buffer_array.append(1)
                elif str(temp_results['gesture'].value) == '2':
                    self.buffer_array.append(2)
                    #print(self.out_array)
                    
            else:
                self.buffer_array.append(0)
                
            if len(self.buffer_array) == 3:
                gesture_max = max(set(self.buffer_array), key = self.buffer_array.count)
                print(self.buffer_array)
                self.buffer_array = []
            else:
                gesture_max = 0
                    
            if gesture_max!=0:
                f = open('./write/feed_gesture_temp.txt', 'w')
                #x = json.dumps(self.feedback_gesture['gesture'])
                f.write(str(gesture_max))
                f.close()

            else:
                f = open('./write/feed_gesture_temp.txt',
                         'w')
                # x = json.dumps(self.feedback_gesture['gesture'])
                f.write(str(None))
                f.close()
                
            #print(self.feedback_gesture['gesture'])
            '''
            if self.feedback_gesture['gesture'] is not None:
                f = open('./write/feed_gesture_temp.txt', 'w')
                #x = json.dumps(self.feedback_gesture['gesture'])
                f.write(str(self.feedback_gesture['gesture'].value))
                f.close()

            else:
                f = open('./write/feed_gesture_temp.txt',
                         'w')
                # x = json.dumps(self.feedback_gesture['gesture'])
                f.write(str(self.feedback_gesture['gesture']))
                f.close()
            '''
            cv2_image = cv2.flip(array2d, 1) # result.get('image')

            livestream_image = Image.fromarray(cv2_image)
            livestream_image = livestream_image.resize((self.config.image_feedback_size_x, self.config.image_feedback_size_y))

            livestream_image_tk = ImageTk.PhotoImage(livestream_image)

            self.feedback_livestream_image_q.put(livestream_image_tk)

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




        except Exception:
            LOGGER.critical(f"Exception")
            LOGGER.critical(f"-" * 60)
            LOGGER.critical(traceback.print_exc)
            traceback.print_exc(file=sys.stdout)
            LOGGER.critical(f"-" * 60)
            os._exit(1)

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

