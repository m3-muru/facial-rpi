import requests
import time
import threading
import configparser
from pathlib import Path
import socket
import datetime
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
    APP_STATUS_URL = config.get(ACTIVE_ENV, 'restapi.APP_STATUS_URL')  # You'll need to add this to your config

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
    def init_app_status_heartbeat(station_id="default_station", interval_seconds=60):
        """
        Initialize continuous app status heartbeat
        """
        def _send_heartbeat():
            while True:
                try:
                    DatabaseHandler.send_app_status_ping(station_id)
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


def main():
    LOGGER.debug(DatabaseHandler.config.get('development', 'restapi.GET_FACEPRINT_URL'))
    LOGGER.debug(DatabaseHandler.config.get('development', 'restapi.ADD_FACEPRINT_URL'))
    LOGGER.debug(DatabaseHandler.config.get('development', 'restapi.PING_URL'))
    LOGGER.debug(DatabaseHandler.config.get('development', 'authentication.some_value'))

    # Test the new app status ping functionality
    DatabaseHandler.send_app_status_ping("test_station_001")
    
    # Start continuous heartbeat (for testing)
    DatabaseHandler.init_app_status_heartbeat("test_station_001", 30)  # Every 30 seconds
    
    # Keep main thread alive for testing
    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()