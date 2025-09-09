import os
import time
from datetime import date, datetime
import threading
import json
import queue
import requests

import rsid_py
from src.processor.face_detection_status import FaceDetectionStatus
from src.processor.face_detection_msg import FaceDetectionMessage
from src.network_comms.database_handler import DatabaseHandler
# from src.processor.gesture_processor import GestureProcessor
import src.logger.custom_logger as custom_logger

LOGGER = custom_logger.get_logger()


class FaceProcessor(threading.Thread):
    MODE_ENROLMENT = 1
    MODE_AUTHENTICATION = 2
    VALID_FP_MODE = {
        MODE_ENROLMENT,
        MODE_AUTHENTICATION
    }

    def __init__(
            self, parent, cmd_request_q, ready_status_q, feedback_msg_q,
            not_used_q, feedback_livestream_detections_q, config, processor_mode,
            socket_handler=None
    ):
        LOGGER.info("FaceProcessor init...")
        super().__init__()

        self.parent = parent

        self.DB_FACEPRINTS = None
        self.init_processor_mode(processor_mode)
        
        self.START_DELAY = 5
        self.START_COUNTDOWN = 1

        # Responsibility: configuration class
        self.PORT = config.PORT
        self.config = config
        # Responsibility: main class
        self.cmd_request_q = cmd_request_q
        self.ready_status_q = ready_status_q
        # Responsibility: image processor class
        self.feedback_livestream_detections_q = feedback_livestream_detections_q

        self.feedback_msg_q = feedback_msg_q
        self.not_used_q = not_used_q
        # Purpose: to store faces detected along with a status from the live stream
        self.livestream_detections = []  # initializing

        self.ETC_IN = 1
        self.ETC_OUT = 2
        self.ETC_STATUS = self.ETC_OUT
        
        self.feedback_gesture = None

        self.entry_timestamp = None
        self.same_employee_id_detections = []
        self.resync_date = ""

        self.cmd_exec = {
            'resync': self.resync,
            'authenticate': self.face_authenticate,
            'enrol': self.face_enroll,
            'd': self.remove_all_users,
            'quit': self.exit_app,
            # 'authenticate_with_gesture': self.face_authenticate_with_gesture
        }

        self.socket_handler = socket_handler

        self.summarized_face_processor_feedback = []

        LOGGER.info("FaceProcessor init complete.")

    def init_processor_mode(self, processor_mode):
        if processor_mode not in FaceProcessor.VALID_FP_MODE:
            LOGGER.error(f'Invalid face processor mode supplied')
            self.parent.exit()

        if processor_mode == FaceProcessor.MODE_AUTHENTICATION:
            self.DB_FACEPRINTS = self.get_faceprint_records_from_remote_db()
        else:
            if not DatabaseHandler.is_ailanthus_alive():
                LOGGER.error(f'Unable to establish connection to Ailanthus server')
                self.parent.exit()

    def run(self):
        
        # self.send_feedback_msg(f'Warning: Please step back ⌛', FaceDetectionStatus.REJECTED)
        # time.sleep(self.START_DELAY)
        # Initial warning message
        self.send_feedback_msg("Warning: Please step back ⏳", FaceDetectionStatus.REJECTED)
        time.sleep(self.START_DELAY)
        self.send_feedback_msg("Face Authentication Begins in 5 Seconds", FaceDetectionStatus.REJECTED)
        time.sleep(2)
 
        # Countdown timer with feedback messages
        countdown_seconds = 5
        for seconds_left in range(countdown_seconds, 0, -1):
 
            status = FaceDetectionStatus.ACCEPTED
 
            self.send_feedback_msg(
                f"{seconds_left}", status
            )
            time.sleep(self.START_COUNTDOWN)
 
        # Authentication begins
        self.send_feedback_msg("Authentication Begins", FaceDetectionStatus.ACCEPTED)
        LOGGER.info("FaceProcessor started.")
        self.init_ready_state(0)
        LOGGER.info("Test starting now") 
        while True:
            self.poll_cmd_request_q()
            self.init_ready_state()
            
    
    def time_difference(first_entry,repeat_entry):
        time_format = '%Y-%m-%d %H:%M:%S'
        str_date_time = first_entry.strftime(time_format)
        tstamp1 = datetime.strptime(str_date_time, time_format)
        print(tstamp1)

        str_date_time2 = repeat_entry.strftime(time_format)
        tstamp2 = datetime.strptime(str_date_time2, time_format)
        print(tstamp2)
        
        if tstamp1 > tstamp2:
            td = tstamp1 - tstamp2
        else:
            td = tstamp2 - tstamp1
        td_seconds = int(td.total_seconds())
        
        return td_seconds

    @staticmethod
    def set_device_config(face_authenticator, custom_device_config=None):
        """
        Setup device config before enrolment/authentication takes place.
        :param str face_authenticator: current face authenticator to be configured used for the enrolment/authentication process
        :param str custom_device_config: set to True to make custom config take effect
        """
        # Available config:
        # https://github.com/IntelRealSense/RealSenseID/blob/master/wrappers/python/face_auth_py.cc#L397-L415
        # Config types and explanation:
        # https://github.com/IntelRealSense/RealSenseID#device-configuration-api
        if custom_device_config:
            LOGGER.face_rec("Device config to be used: custom")
            new_device_config = rsid_py.DeviceConfig()

            # Modify the custom config to your liking below
            new_device_config.camera_rotation = rsid_py.CameraRotation.Rotation_180_Deg
            new_device_config.security_level = rsid_py.SecurityLevel.High
            new_device_config.algo_flow = rsid_py.AlgoFlow.All
            new_device_config.face_selection_policy = rsid_py.FaceSelectionPolicy.All
            face_authenticator.set_device_config(new_device_config)
            device_config = face_authenticator.query_device_config()
        else:
            LOGGER.face_rec("Device config to be used: default")
            new_device_config = rsid_py.DeviceConfig()
            new_device_config.camera_rotation = rsid_py.CameraRotation.Rotation_0_Deg
            new_device_config.security_level = rsid_py.SecurityLevel.Medium
            new_device_config.algo_flow = rsid_py.AlgoFlow.All
            new_device_config.face_selection_policy = rsid_py.FaceSelectionPolicy.Single
            face_authenticator.set_device_config(new_device_config)
            device_config = face_authenticator.query_device_config()
        LOGGER.face_rec(f"Final device config preview: {device_config}")

    def get_faceprint_records_from_remote_db(self):
        try:
            get_response = DatabaseHandler.get_faceprints()
        except requests.exceptions.RequestException as e:
            LOGGER.error(f'Exception occurred during retrieval of FacePrint records from DB: {e}')
            self.parent.exit()

        json_dict = get_response.json()
        
        # new_json_dict = {"faceprint_records":json_dict}
        # faceprint_records = new_json_dict.get("faceprint_records")
        
        faceprint_records = json_dict.get("faceprint_records")

        LOGGER.face_rec(f'Total FacePrint records retrieved from DB: {len(faceprint_records)}')

        finalized_faceprint_dict = {}
        for faceprint_record in faceprint_records:
            # Retrieve current iteration's employee ID
            iteration_employee_id = faceprint_record.get("employee_id")

            # Create "rsid_py.Faceprints" type object with faceprint properties retrieved from DB
            faceprint_object = rsid_py.Faceprints()
            faceprint_object.version = faceprint_record.get("version")
            faceprint_object.features_type = faceprint_record.get("features_type")
            faceprint_object.flags = faceprint_record.get("flags")
            faceprint_object.adaptive_descriptor_nomask = faceprint_record.get("adaptive_descriptor_nomask")
            faceprint_object.adaptive_descriptor_withmask = faceprint_record.get("adaptive_descriptor_withmask")
            faceprint_object.enroll_descriptor = faceprint_record.get("enroll_descriptor")

            # If current iteration employee ID is not detected in finalized finalized_faceprint_dict
            if iteration_employee_id not in finalized_faceprint_dict:
                # Create a new dict entry with the key being the iteration employee ID and
                #  the value being a list to store faceprint objects for the employee ID
                finalized_faceprint_dict[iteration_employee_id] = []
                # Add the created faceprint object into the list
                finalized_faceprint_dict.get(iteration_employee_id).append(faceprint_object)
            else:
                # Else the faceprint object into the list of the existing employee ID
                finalized_faceprint_dict.get(iteration_employee_id).append(faceprint_object)
        return finalized_faceprint_dict

    # The meaning of "processed" here refers to the authentication of a face. Whether it was deemed to be a
    # legit or spoof face. The "authentication of a face" has nothing to do with "face matching".
    # These are 2 totally different thing altogether.
    def send_feedback_livestream_faces_processed(self, status):
        # Find the latest detected face and attach a processing status to it
        for f in self.livestream_detections:  # Processing
            # If current iteration's processing status is PENDING, means it is the one we are targeting
            if f.get("status") is FaceDetectionStatus.PENDING:
                # Update processing status to either "SUCCESS" or "FAILURE" based on its auth results. Doing so also:
                # 1. Indicates that this face has already been processed
                # 2. Trigger image_processor.py to drawing appropriately colored bounding box around the face based on
                #   its processing status
                f['status'] = status
                break
        LOGGER.face_rec(f'Detections queued: on result')
        self.feedback_livestream_detections_q.put(self.livestream_detections)

    def send_feedback_msg(self, msg='Warning: missing feedback msg', face_process_status=None):
        self.feedback_msg_q.put(
            {
                "msg": msg,
                "status": face_process_status
            }
        )
        self.summarized_face_processor_feedback.append(msg)

    # face_auth_status:
    # https://github.com/IntelRealSense/RealSenseID/blob/master/wrappers/python/face_auth_py.cc#L317
    # detection_faceprint:
    # https://github.com/IntelRealSense/RealSenseID/blob/master/wrappers/python/face_auth_py.cc#L539
    # authenticator:
    # https://github.com/IntelRealSense/RealSenseID/blob/master/wrappers/python/face_auth_py.cc#L593

    def on_fp_auth_result(self, face_auth_status, detection_faceprint, authenticator):
        auth_status_msg_str = str(face_auth_status)
        auth_status_msg = FaceDetectionMessage.cleanup_msg(auth_status_msg_str)
        LOGGER.face_rec(f'Final results concluded for detected Face: {"Ok" if "Success" in auth_status_msg_str else "Not Ok"} ---> {auth_status_msg_str}')

        # If face detected is an invalid face (spoofing, face too tilted, no face, error), no relation to matched auth!
        #   1. Update status bar
        #   2. Set determination status for detection box color
        if face_auth_status != rsid_py.AuthenticateStatus.Success:
            LOGGER.face_rec(f'Forbidden: {auth_status_msg}')
            # self.send_feedback_msg(f'Forbidden: {auth_status_msg}', FaceDetectionStatus.REJECTED)
            self.send_feedback_livestream_faces_processed(FaceDetectionStatus.REJECTED)
            time.sleep(1)
            self.send_feedback_msg(f'Ready')
            return

        max_score = -100
        selected_user = None
        # Match auth logic begin
        # Iterate over each employee record
        for employee_id, faceprint_list in self.DB_FACEPRINTS.items():
            # Iterate over each faceprint object in the faceprint list belonging to the current employee
            for faceprint in faceprint_list:
                updated_faceprints = rsid_py.Faceprints()

                # Perform matching on detection faceprint against record faceprint
                match_result = authenticator.match_faceprints(detection_faceprint, faceprint, updated_faceprints)
                LOGGER.face_rec(f'Comparison with {employee_id}: score={match_result.score}')

                # If current match is success
                if match_result.success:
                    # If current match has a higher score than the previous match
                    if match_result.score > max_score:
                        # If current match's score is higher or equal to the required min threshold for authentication
                        if match_result.score >= self.config.min_auth_score_threshold:
                            # Update and keep track of the highest matched score thus far
                            max_score = match_result.score
                            selected_user = employee_id

        if selected_user is not None:
            LOGGER.face_rec(f'Success, Matched user: "{selected_user}", Score: {max_score}')
            self.send_feedback_msg( f'{selected_user}', FaceDetectionStatus.ACCEPTED)
            time.sleep(1)  
            # , Gesture:{self.feedback_gesture}', FaceDetectionStatus.ACCEPTED)
            self.send_feedback_msg(f'Ready')
            self.send_feedback_livestream_faces_processed(FaceDetectionStatus.ACCEPTED)
            if self.socket_handler is not None:
                #Edit ETC in or out here
                self.socket_handler.broadcast_to_clients(selected_user, self.ETC_STATUS)
        else:
            LOGGER.face_rec(f'Forbidden: No matching user found')
            self.send_feedback_msg(
                f'#8: Forbidden: No matching user found', FaceDetectionStatus.REJECTED
            )
            self.send_feedback_livestream_faces_processed(FaceDetectionStatus.REJECTED)
            time.sleep(1)
            self.send_feedback_msg(f'Ready')

    # def face_authenticate(self):
        
    #     while True:
    #         self.summarized_face_processor_feedback.clear()
    #         LOGGER.face_rec('Face authentication triggered')
    #         if len(self.DB_FACEPRINTS) == 0:
    #             LOGGER.face_rec('No faceprints detected in sys. Pls Enroll an employee or Resync')
    #             self.send_feedback_msg("No faceprints in sys. Pls Enroll an employee or Resync", FaceDetectionStatus.REJECTED)
    #         else:
    #             with rsid_py.FaceAuthenticator(self.PORT) as authenticator:
    #                 FaceProcessor.set_device_config(authenticator)
    #                 self.ready_status_q.put(False)
    #                 LOGGER.face_rec('Authenticating..')
    #                 # self.send_feedback_msg("Authenticating..")
    #                 authenticator.extract_faceprints_for_auth(
    #                     on_result=
    #                     lambda face_auth_status,
    #                     detection_faceprint: self.on_fp_auth_result(face_auth_status, detection_faceprint, authenticator),
    #                     on_hint=self.on_hint,
    #                     on_faces=self.on_faces
    #                 )
    #         time.sleep(3)
    
    # def face_authenticate(self):
        
    #     LOGGER.face_rec('Waiting for face detection...')
    #     with rsid_py.FaceAuthenticator(self.PORT) as authenticator:
    #         FaceProcessor.set_device_config(authenticator)
            
    #         def on_result(face_auth_status, detection_faceprint):
                
    #             if detection_faceprint is not None: 
    #                 print(detection_faceprint)
    #                 LOGGER.face_rec('Face detected. Authentication triggered')
    #                 if len(self.DB_FACEPRINTS) == 0:
    #                     LOGGER.face_rec('No faceprints detected in sys. Pls Enroll an employee or Resync')
    #                     self.send_feedback_msg("No faceprints in sys. Pls Enroll an employee or Resync", FaceDetectionStatus.REJECTED)
    #                 else:
    #                     self.ready_status_q.put(False)
    #                     LOGGER.face_rec('Authenticating..')
    #                     # Proceed with authentication using the detected faceprint
    #                     self.perform_authentication(authenticator, face_auth_status, detection_faceprint)
                    


    #         def on_hint(hint):
    #             self.on_hint(hint)

    #         def on_faces(faces, timestamp):
    #             self.on_faces(faces, timestamp)

    #         # Start the face detection process
    #         while True:
    #             authenticator.extract_faceprints_for_auth(
    #                 on_result=on_result,
    #                 on_hint=on_hint,
    #                 on_faces=on_faces
    #             )
    #             time.sleep(3)

    # def perform_authentication(self, authenticator, face_auth_status, detection_faceprint):
    #         self.summarized_face_processor_feedback.clear()
    #         self.on_fp_auth_result(face_auth_status, detection_faceprint, authenticator)
    #         time.sleep(1.5)
    #         self.livestream_detections.clear()

    def face_authenticate(self):
        LOGGER.face_rec('Waiting for face detection...')
        with rsid_py.FaceAuthenticator(self.PORT) as authenticator:
            FaceProcessor.set_device_config(authenticator)
            
            def on_result(face_auth_status, detection_faceprint):
                if detection_faceprint is not None:
                    LOGGER.face_rec('Face detected. Authentication triggered')
                    if len(self.DB_FACEPRINTS) == 0:
                        LOGGER.face_rec('No faceprints detected in sys. Pls Enroll an employee or Resync')
                        self.send_feedback_msg("No faceprints in sys. Pls Enroll an employee or Resync", FaceDetectionStatus.REJECTED)
                    else:
                        self.ready_status_q.put(False)
                        LOGGER.face_rec('Authenticating..')
                        self.send_feedback_msg("Authenticating..")
                        self.perform_authentication(authenticator, face_auth_status, detection_faceprint)

            def on_hint(hint):
                self.on_hint(hint)

            def on_faces(faces, timestamp):
                self.on_faces(faces, timestamp)

            while True:
                if datetime.now().hour == 16 and datetime.now().minute == 10 and str(date.today()) != self.resync_date:
                    self.resync_date = str(date.today())
                    # LOGGER.info("Test started") 
                    self.resync()
                get_feedback_gesture = open('./write/feed_fd_temp.txt', 'r')
                self.feedback_gesture = get_feedback_gesture.readline().strip()
                get_feedback_gesture.close()

                if self.feedback_gesture in ['True', '2']:
                    LOGGER.face_rec(f'{"Face" if self.feedback_gesture == "True" else "Gesture"} Detected: "{self.feedback_gesture}"')
                    self.summarized_face_processor_feedback.clear()
                    authenticator.extract_faceprints_for_auth(
                        on_result=on_result,
                        on_hint=on_hint,
                        on_faces=on_faces
                    )
                time.sleep(0.5)

    def perform_authentication(self, authenticator, face_auth_status, detection_faceprint):
        self.on_fp_auth_result(face_auth_status, detection_faceprint, authenticator)
        time.sleep(0.5)
        self.livestream_detections.clear()

    # face_auth_status:
    # https://github.com/IntelRealSense/RealSenseID/blob/master/wrappers/python/face_auth_py.cc#L346
    # detection_faceprint:
    # https://github.com/IntelRealSense/RealSenseID/blob/master/wrappers/python/face_auth_py.cc#L539
    def on_fp_enroll_result(self, face_auth_status, detection_faceprint, employee_id):
        enroll_status_msg_str = str(face_auth_status)
        enroll_status_msg = FaceDetectionMessage.cleanup_msg(enroll_status_msg_str)
        LOGGER.face_rec(f'Final results concluded for detected Face: {"Ok" if "Success" in enroll_status_msg_str else "Not Ok"} ---> {enroll_status_msg_str}')

        # If face detected is an invalid face (spoofing, face too tilted, no face, error), no relation to matched auth!
        #   1. Set determination status for detection box color
        if face_auth_status != rsid_py.EnrollStatus.Success:
            LOGGER.face_rec(f'{enroll_status_msg}')
            self.send_feedback_msg(enroll_status_msg, FaceDetectionStatus.REJECTED)
            self.send_feedback_livestream_faces_processed(FaceDetectionStatus.REJECTED)
            return

        enroll_status_msg = enroll_status_msg + f", Employee ID: {employee_id}"
        LOGGER.face_rec(f'{enroll_status_msg}')
        self.send_feedback_msg(enroll_status_msg, FaceDetectionStatus.ACCEPTED)
        self.send_feedback_livestream_faces_processed(FaceDetectionStatus.ACCEPTED)

        # Create dict object to be saved into the DB through REST api as a JSON string
        fp_dict = {
            "employee_id": employee_id,
            "version": detection_faceprint.version,
            "features_type": detection_faceprint.features_type,
            "flags": detection_faceprint.flags,
            "adaptive_descriptor_nomask": detection_faceprint.features,
            "adaptive_descriptor_withmask": [0] * 259,
            "enroll_descriptor": detection_faceprint.features
        }
        self.add_faceprint_records_into_remote_db(fp_dict)

    def add_faceprint_records_into_remote_db(self, faceprint_dict):
        try:
            # Invoke method to save created dict into DB
            DatabaseHandler.add_faceprint(faceprint_dict)
        except requests.exceptions.RequestException as e:
            LOGGER.error(f'Exception occurred during insertion of FacePrint records into DB: {e}')
            self.parent.exit()

    def face_enroll(self, user_id=f'user_{int(time.time() / 1000)}'):
        LOGGER.face_rec('Face enrolment triggered')
        self.summarized_face_processor_feedback.clear()
        with rsid_py.FaceAuthenticator(self.PORT) as authenticator:
            FaceProcessor.set_device_config(authenticator)
            self.ready_status_q.put(False)
            LOGGER.face_rec(f'Enrolling...')
            self.send_feedback_msg("Enrolling...")
            authenticator.extract_faceprints_for_enroll(
                on_result=
                lambda face_auth_status, detection_faceprint:
                self.on_fp_enroll_result(face_auth_status, detection_faceprint, user_id),
                on_progress=self.on_progress,
                on_hint=self.on_hint,
                on_faces=self.on_faces
            )

    def remove_all_users(self):
        with rsid_py.FaceAuthenticator(self.PORT) as f:
            LOGGER.face_rec(f'Remove...')
            self.send_feedback_msg("Remove..")
            f.remove_all_users()
            LOGGER.face_rec(f'Remove Success')
            self.send_feedback_msg("Remove Success")

    def on_progress(self, p):
        LOGGER.face_rec(f'on_progress() - p: {p}')
        self.send_feedback_msg(f'On progress {p}')

    # https://github.com/IntelRealSense/RealSenseID/blob/master/wrappers/python/face_auth_py.cc#L346
    def on_hint(self, face_detection_status):
        face_detection_status_str = str(face_detection_status)

        LOGGER.face_rec(f'Checking detected Face for spoof attacks...')
        self.send_feedback_msg(f'Checking detected Face for spoof attacks...')

        if "Success" not in face_detection_status_str:
            face_detection_status_str = FaceDetectionMessage.cleanup_msg(face_detection_status_str)
            self.send_feedback_msg(f'{face_detection_status_str}')

        LOGGER.face_rec(f'Detected face status: {"Ok" if "Success" in face_detection_status_str else "Not Ok"} ---> {face_detection_status}')

    # Register detected rsid_py.FaceRect(s) from live stream into array
    # NOTE: This function will only be invoked DURING enrolment OR authentication, meaning
    #   on normal circumstances, there will not be any detected faces
    def on_faces(self, faces, timestamp):
        # For each faces detected:
        # 1. create a dict{}
        # 2. set the face detected (x,y coordinates) key value
        # 3. set the current detection status key value as PENDING
        # 4. add the created dict into a list[]
        # 5. finally, using the computed list[] of dict for all faces, overwrite the detected_faces list[]
        self.livestream_detections = [  # Processing
            {
                'face': f,
                'status': FaceDetectionStatus.PENDING
            } for f in faces
        ]
        LOGGER.face_rec(f'Detections queued: on pending')
        self.feedback_livestream_detections_q.put(self.livestream_detections)

    def exit_app(self):
        LOGGER.info(f'Application exiting...')
        self.send_feedback_msg('Bye.. :)')
        time.sleep(0.4)
        os._exit(0)

    def resync(self):
        self.DB_FACEPRINTS = self.get_faceprint_records_from_remote_db()

    def init_ready_state(self, delay=2.5):
        LOGGER.face_rec(f"Init-ing ready state in: {delay} seconds")
        time.sleep(delay)

        # NOTE: The time.sleep(delay) executed before the statements below is done on purpose for better user
        #   experience, reason is because we have to show user the detected border and employee ID feedback for
        #   X number of seconds before clearing it.
        #   Instantly doing the above-mentioned causes negative user experience as the app moves "too fast".

        # The statement executed below will remove the detection border drawn on the image
        LOGGER.face_rec(f'Clearing all active detection (total=[{len(self.livestream_detections)}]) now...')
        self.livestream_detections = []
        LOGGER.face_rec(f'Detections queued: on cleared')
        self.feedback_livestream_detections_q.put(self.livestream_detections)

        # The statement executed below will feedbacks onto the GUI status bar that the app is ready
        LOGGER.face_rec(f'Face Processor Ready')
        self.send_feedback_msg("Ready")

        # The statement executed below will enable the locked button interface on the GUI app
        self.ready_status_q.put(True)
        
        LOGGER.debug(f'summarized_face_processor_feedback: {self.summarized_face_processor_feedback}')

    def poll_cmd_request_q(self):
        # Get a command from the queue. This blocks the thread until a command is passed to the queue
        request_dict = self.cmd_request_q.get()
        self.ready_status_q.put(False)
        command = request_dict.get("command")

        # Retrieve function corresponding to the command received
        func_call = self.cmd_exec.get(command, lambda: None)

        # Ensure the function exists
        if callable(func_call) and func_call.__name__ != "<lambda>":
            # If function's name retrieved is the related to enrolment
            if func_call.__name__ == "face_enroll":
                # Need to explicitly retrieve employee ID
                employee_id = request_dict.get("employee_id")
                # And pass it as an argument
                func_call(employee_id)
            # Else
            else:
                # Just invoke function normally
                func_call()
        else:
            LOGGER.error(f'Invoking cmd request failed. No such function "{command}" exists. >>>{func_call.__name__}')


def get_device_port():
    from datetime import date, datetime
    import serial.tools.list_ports
    import json
    ports = serial.tools.list_ports.comports()

    com_port = None

    dump_data = []
    with open("../../log/device/device_tracing.json", "a+") as json_file:
        json_file.seek(0)
        try:
            dump_data = json.load(json_file)
        except:
            pass

    for port in ports:
        _dict = port.__dict__
        # print(port)
        # pprint(port.__dict__, indent=4)
        if 'Bluetooth' not in port.description:
            _dict["connection_date"] = date.today().strftime("%d/%m/%y")
            _dict["connection_time"] = datetime.now().strftime("%H:%M:%S")
            dump_data.append(_dict)
        if 'USB VID:PID=2AAD:6373' in port.hwid:
            com_port = port.device

    with open("../../log/device/device_tracing.json", "w", encoding='utf-8') as json_file:
        json.dump(dump_data, json_file, ensure_ascii=False, indent=4, default=str)

    return com_port


def face_enroll_loop(authenticator, enrolment_loop_q, stop_enrolment_loop_q, employee_id):
    def _on_enrolment_loop_result(face_auth_status, detection_faceprint):
        nonlocal enrolment_loop_q
        nonlocal employee_id

        try:
            # ---Beginning of face descriptor extraction logic---
            fp = {
                "employee_id": employee_id,
                "faceprint": {
                    "version": detection_faceprint.version,
                    "features_type": detection_faceprint.features_type,
                    "flags": detection_faceprint.flags,
                    "adaptive_descriptor_nomask": detection_faceprint.features,
                    "adaptive_descriptor_withmask": [0] * 259,
                    "enroll_descriptor": detection_faceprint.features
                }
            }

            fp_json_str = json.dumps(fp)
            enrolment_loop_q.put(fp_json_str)
            print(f"{fp_json_str}")
        except Exception as e:
            print(f"e: {e}")

    def _on_hint(h):
        # TODO: provide status message feedback
        # print(f"\n\n\n on_hint():\t h: {h} \n\n\n")
        return

    def _on_faces(f, i):
        # TODO: draw feedback on screen
        # print(f"\n\n\n _on_faces():\t f: {f}, i: {i} \n\n\n")
        return

    while True:
        try:
            stop_enrolment_loop_q.get_nowait()
        except queue.Empty:
            authenticator.extract_faceprints_for_enroll(
                on_result=
                lambda face_auth_status, detection_faceprint:
                    _on_enrolment_loop_result(face_auth_status, detection_faceprint),

                on_hint=_on_hint,

                on_faces=_on_faces
            )
            time.sleep(0.2)
        else:
            return


def generate_auth_result(authenticator, enrolment_result, auth_result_q):
    auth_result = {
        "best_score": None,
        "best_index": None,
        "list": []
    }
    auth_success_q = queue.Queue()

    def _on_auth_result(face_auth_status, detection_faceprint):
        nonlocal authenticator
        nonlocal enrolment
        nonlocal auth_result
        nonlocal auth_success_q

        if face_auth_status != rsid_py.AuthenticateStatus.Success:
            auth_success_q.put(False)
            return

        enrolment_o = json.loads(enrolment)
        enrolment_properties = enrolment_o["faceprint"]
        enrolment_faceprints = rsid_py.Faceprints()
        enrolment_faceprints.version = enrolment_properties["version"]
        enrolment_faceprints.features_type = enrolment_properties["features_type"]
        enrolment_faceprints.flags = enrolment_properties["flags"]
        enrolment_faceprints.adaptive_descriptor_nomask = enrolment_properties["adaptive_descriptor_nomask"]
        enrolment_faceprints.adaptive_descriptor_withmask = enrolment_properties["adaptive_descriptor_withmask"]
        enrolment_faceprints.enroll_descriptor = enrolment_properties["enroll_descriptor"]

        updated_faceprints = rsid_py.Faceprints()
        match_result = authenticator.match_faceprints(detection_faceprint, enrolment_faceprints, updated_faceprints)

        if match_result.success:
            auth_result["list"].append({
                "enrolment": enrolment,
                "match_result": match_result,
                "score": match_result.score
            })
            auth_success_q.put(True)
        else:
            auth_success_q.put(False)
        return

    def _on_hint(authenticate_status):
        return

    def _on_faces(faces, timestamp):
        return

    for enrolment in enrolment_result:
        auth_success = False
        while not auth_success:
            authenticator.extract_faceprints_for_auth(
                on_result=
                lambda face_auth_status, detection_faceprint:
                _on_auth_result(face_auth_status, detection_faceprint),
                on_hint=_on_hint,
                on_faces=_on_faces
            )
            auth_success = auth_success_q.get()

    best_score = 0
    best_index = None
    for i, item in enumerate(auth_result["list"]):
        score = item["score"]
        if score > best_score:
            best_index = i
            best_score = score

    auth_result["best_score"] = best_score
    auth_result["best_index"] = best_index
    auth_result_q.put(auth_result)


def main():
    employee_id = "Bob the builder"
    facial_config = {
        "min_auth_score_threshold": 2500,
        "min_enroll_score_threshold": 2500,
        "enroll_best_out_of": 3
    }

    with rsid_py.FaceAuthenticator(get_device_port()) as authenticator:
        FaceProcessor.set_device_config(authenticator)

        enrolment_loop_q = queue.Queue()
        stop_enrolment_loop_q = queue.Queue()
        on_demand_cancel_q = queue.Queue()

        def _poll_on_demand_cancellation():
            nonlocal authenticator
            nonlocal on_demand_cancel_q
            print("polling for on demand cancellation")
            on_demand_cancel_q.get()
            authenticator.cancel()

        # TODO: begin cancel queue thread here on authenticator to block on thread and check for on demand cancellation
        threading.Thread(target=lambda: _poll_on_demand_cancellation(), daemon=True).start()

        threading.Thread(target=lambda: face_enroll_loop(authenticator, enrolment_loop_q, stop_enrolment_loop_q, employee_id), daemon=True).start()
        enrolment_result = []
        while True:
            enrolment_result.append(enrolment_loop_q.get())
            if len(enrolment_result) == facial_config["enroll_best_out_of"]:
                stop_enrolment_loop_q.put(True)
                break

        # Wait awhile for things to resolve before continuing
        time.sleep(0.5)
        print(f"Final result:")
        for result in enrolment_result:
            print(result)

        print("BEGIN AUTH COMPARISONS")
        auth_result_q = queue.Queue()
        threading.Thread(
            target=lambda: generate_auth_result(authenticator, enrolment_result, auth_result_q),
            daemon=True).start()

        auth_result = None
        while auth_result is None:
            time.sleep(0.5)
            try:
                auth_result = auth_result_q.get_nowait()
            except queue.Empty:
                pass

        auth_result_list = auth_result["list"]
        for i, item in enumerate(auth_result_list):
            print()
            print(f'[{i}]enrolment: {item["enrolment"]}')
            print(f'[{i}]match_result: {item["match_result"]}')
            print(f'[{i}]score: {item["score"]}')
        print(f'\nBest score: {auth_result["best_score"]}')
        print(f'Best index: {auth_result["best_index"]}')
        #   print(f"Enrolling: {employee id}, score: {auth_result.best}")

if __name__ == '__main__':

    main()

