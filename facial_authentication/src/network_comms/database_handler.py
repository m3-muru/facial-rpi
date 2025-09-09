import requests
import time
import threading
import configparser
from pathlib import Path
import socket
import datetime
import json
import src.logger.custom_logger as custom_logger

LOGGER = custom_logger.get_logger()


class DatabaseHandler:
    PROJECT_ROOT_DIR = str(Path(__file__).parent.parent.parent)
    config = configparser.RawConfigParser()
    config.read(PROJECT_ROOT_DIR + '/environment_config.ini')
    ACTIVE_ENV = config.get('INIT', 'ACTIVE_ENV')
    LOGGER.debug(f'Active Environment: {ACTIVE_ENV}')

    GET_FACEPRINT_URL = config.get(ACTIVE_ENV, 'restapi.GET_FACEPRINT_URL')
    ADD_FACEPRINT_URL = config.get(ACTIVE_ENV, 'restapi.ADD_FACEPRINT_URL')
    PING_URL = config.get(ACTIVE_ENV, 'restapi.PING_URL')
    
    # Add new endpoint for app status reporting
    try:
        APP_STATUS_URL = config.get(ACTIVE_ENV, 'restapi.APP_STATUS_URL')
    except:
        APP_STATUS_URL = None
        LOGGER.warning("APP_STATUS_URL not found in config, app status reporting disabled")
    
    # ETCMon integration
    try:
        ETCMON_URL = config.get(ACTIVE_ENV, 'etcmon.SERVER_URL')
        ETCMON_ENABLED = config.getboolean(ACTIVE_ENV, 'etcmon.ENABLED')
    except:
        ETCMON_URL = None
        ETCMON_ENABLED = False
        LOGGER.info("ETCMon configuration not found, ETCMon integration disabled")

    @staticmethod
    def get_faceprints():
        try:
            response = requests.get(DatabaseHandler.GET_FACEPRINT_URL, verify=False, headers={"x-api-key":"OA7A1kuHiI"})
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException:
            raise

    @staticmethod
    def add_faceprint(fp_dict):
        try:
            response = requests.post(DatabaseHandler.ADD_FACEPRINT_URL, json=fp_dict, verify=False, headers={"x-api-key":"OA7A1kuHiI"})
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(e)

    @staticmethod
    def ping():
        try:
            response = requests.get(DatabaseHandler.PING_URL, verify=False)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException:
            raise

    @staticmethod
    def is_ailanthus_alive():
        try:
            return True if DatabaseHandler.ping().status_code == 200 else False
        except requests.exceptions.RequestException as e:
            return False

    @staticmethod
    def send_app_status_ping(station_id="default_station"):
        """
        Send app status ping to server to indicate this app instance is alive
        """
        try:
            # Skip if APP_STATUS_URL is not configured
            if not DatabaseHandler.APP_STATUS_URL:
                LOGGER.debug("APP_STATUS_URL not configured, skipping app status ping")
                return None
                
            # Gather system information
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            current_time = datetime.datetime.now()
            
            status_data = {
                "station_id": station_id,
                "hostname": hostname,
                "ip_address": local_ip,
                "timestamp": current_time.isoformat(),
                "status": "alive",
                "app_version": "1.0.0",  # You can make this configurable
                "last_ping": current_time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            LOGGER.info(f"Sending app status ping: {status_data}")
            
            response = requests.post(
                DatabaseHandler.APP_STATUS_URL, 
                json=status_data, 
                verify=False,
                headers={"x-api-key": "OA7A1kuHiI"}  # Use same API key
            )
            response.raise_for_status()
            
            LOGGER.info(f"App status ping sent successfully. Response: {response.status_code}")
            return response
            
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"Failed to send app status ping: {e}")
            return None

    @staticmethod
    def send_etcmon_heartbeat(station_id="default_station", additional_data=None):
        """
        Send heartbeat to ETCMon monitoring system
        """
        try:
            if not DatabaseHandler.ETCMON_ENABLED or not DatabaseHandler.ETCMON_URL:
                LOGGER.debug("ETCMon not configured, skipping heartbeat")
                return None
                
            # Gather system information
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            current_time = datetime.datetime.now()
            
            heartbeat_data = {
                "station_id": station_id,
                "hostname": hostname,
                "ip_address": local_ip,
                "timestamp": current_time.isoformat(),
                "status": "online",
                "service_type": "etc_face_recognition",
                "last_heartbeat": current_time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Add any additional data
            if additional_data:
                heartbeat_data.update(additional_data)
            
            LOGGER.debug(f"Sending ETCMon heartbeat: {heartbeat_data}")
            
            response = requests.post(
                f"{DatabaseHandler.ETCMON_URL}/update",
                json=heartbeat_data,
                verify=False,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "ETC-FaceRecognition/1.0"
                },
                timeout=10
            )
            response.raise_for_status()
            
            LOGGER.debug(f"ETCMon heartbeat sent successfully. Response: {response.status_code}")
            return response
            
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"Failed to send ETCMon heartbeat: {e}")
            return None

    @staticmethod
    def init_app_status_heartbeat(station_id="default_station", interval_seconds=60):
        """
        Initialize continuous app status heartbeat
        """
        def _send_heartbeat():
            while True:
                try:
                    # Send to both systems if configured
                    DatabaseHandler.send_app_status_ping(station_id)
                    DatabaseHandler.send_etcmon_heartbeat(station_id)
                    time.sleep(interval_seconds)
                except Exception as e:
                    LOGGER.error(f"Error in app status heartbeat: {e}")
                    time.sleep(interval_seconds)  # Continue trying even if there's an error

        threading.Thread(target=_send_heartbeat, daemon=True).start()
        LOGGER.info(f"App status heartbeat started (interval: {interval_seconds}s, station: {station_id})")

    @staticmethod
    def init_client_heartbeat_checker():
        def _check_client_heartbeat(delay=3):
            time.sleep(delay)
            _check_heartbeat()

        def _check_heartbeat():
            try:
                response = DatabaseHandler.ping()
                LOGGER.debug(
                    f'\nPing response: {response}'
                    f'\nResponse text: {response.text}'
                    f'\nResponse status_code: {response.status_code}'
                )
            except requests.exceptions.RequestException as e:
                LOGGER.error(f'Error: {e}, freezing all activity on application until connection is re-established')

        _check_client_heartbeat(0)
        # Keep spawned child thread alive forever
        while True:
            _check_client_heartbeat()

    @staticmethod
    def spawn_client_heartbeat_checker_thread():
        threading.Thread(target=lambda: DatabaseHandler.init_client_heartbeat_checker(), daemon=True).start()

    @staticmethod
    def report_authentication_event(station_id, employee_id, status, timestamp=None):
        """
        Report authentication events to monitoring systems
        """
        if timestamp is None:
            timestamp = datetime.datetime.now()
            
        event_data = {
            "station_id": station_id,
            "employee_id": employee_id,
            "event_type": "authentication",
            "status": status,  # success, failure, etc.
            "timestamp": timestamp.isoformat(),
            "hostname": socket.gethostname(),
            "ip_address": socket.gethostbyname(socket.gethostname())
        }
        
        # Send to ETCMon if enabled
        if DatabaseHandler.ETCMON_ENABLED and DatabaseHandler.ETCMON_URL:
            try:
                response = requests.post(
                    f"{DatabaseHandler.ETCMON_URL}/event",
                    json=event_data,
                    verify=False,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "ETC-FaceRecognition/1.0"
                    },
                    timeout=5
                )
                LOGGER.info(f"Authentication event reported to ETCMon: {event_data}")
            except Exception as e:
                LOGGER.error(f"Failed to report authentication event to ETCMon: {e}")


def main():
    LOGGER.debug(DatabaseHandler.config.get('development', 'restapi.GET_FACEPRINT_URL'))
    LOGGER.debug(DatabaseHandler.config.get('development', 'restapi.ADD_FACEPRINT_URL'))
    LOGGER.debug(DatabaseHandler.config.get('development', 'restapi.PING_URL'))
    LOGGER.debug(DatabaseHandler.config.get('development', 'authentication.some_value'))

    # Test the new app status ping functionality
    DatabaseHandler.send_app_status_ping("test_station_001")
    
    # Test ETCMon heartbeat
    DatabaseHandler.send_etcmon_heartbeat("test_station_001", {"test_mode": True})
    
    # Start continuous heartbeat (for testing)
    DatabaseHandler.init_app_status_heartbeat("test_station_001", 30)  # Every 30 seconds
    
    # Keep main thread alive for testing
    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()