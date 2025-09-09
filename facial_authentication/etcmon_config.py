# etcmon_config.py
"""
Configuration file for ETCMon Helper and Flask App
Update these values according to your environment
"""

import socket

# Flask Server Configuration
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000
FLASK_DEBUG = False

# ETCMon Server Configuration
ETCMON_SERVER_URL = 'http://your-etcmon-server:8080'  # Update with actual ETCMON server
ETCMON_UPDATE_ENDPOINT = '/update'
ETCMON_API_KEY = 'your-api-key-here'  # If authentication is required

# Client Configuration
CLIENT_NAME = 'lift_lobby_etc01'  # Update with actual client identifier
STATION_LOCATION = 'Main Building - Floor 1'  # Optional: physical location description

# Monitoring Configuration
HEALTH_CHECK_INTERVAL = 5  # seconds
ETCMON_UPDATE_INTERVAL = 30  # seconds
REQUEST_TIMEOUT = 10  # seconds

# System Information (auto-detected)
HOSTNAME = socket.gethostname()
try:
    IP_ADDRESS = socket.gethostbyname(HOSTNAME)
except:
    IP_ADDRESS = '127.0.0.1'

# Logging Configuration
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = 'etcmon_helper.log'
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# Application Paths
ETC_APP_PATH = 'app_authentication.py'
FLASK_APP_PATH = 'flask_app.py'

# Environment-specific configurations
ENVIRONMENTS = {
    'development': {
        'etcmon_server_url': 'http://localhost:8080',
        'debug': True,
        'log_level': 'DEBUG'
    },
    'staging': {
        'etcmon_server_url': 'http://staging-etcmon.company.com:8080',
        'debug': False,
        'log_level': 'INFO'
    },
    'production': {
        'etcmon_server_url': 'http://etcmon.company.com:8080',
        'debug': False,
        'log_level': 'WARNING'
    }
}

# Current environment (change this to switch environments)
CURRENT_ENV = 'development'

def get_config():
    """
    Get configuration for current environment
    """
    base_config = {
        'flask_host': FLASK_HOST,
        'flask_port': FLASK_PORT,
        'flask_debug': FLASK_DEBUG,
        'etcmon_server_url': ETCMON_SERVER_URL,
        'etcmon_update_endpoint': ETCMON_UPDATE_ENDPOINT,
        'etcmon_api_key': ETCMON_API_KEY,
        'client_name': CLIENT_NAME,
        'station_location': STATION_LOCATION,
        'health_check_interval': HEALTH_CHECK_INTERVAL,
        'etcmon_update_interval': ETCMON_UPDATE_INTERVAL,
        'request_timeout': REQUEST_TIMEOUT,
        'hostname': HOSTNAME,
        'ip_address': IP_ADDRESS,
        'log_level': LOG_LEVEL,
        'log_file': LOG_FILE,
        'max_log_size': MAX_LOG_SIZE,
        'log_backup_count': LOG_BACKUP_COUNT,
        'etc_app_path': ETC_APP_PATH,
        'flask_app_path': FLASK_APP_PATH
    }
    
    # Override with environment-specific settings
    if CURRENT_ENV in ENVIRONMENTS:
        env_config = ENVIRONMENTS[CURRENT_ENV]
        base_config.update(env_config)
    
    return base_config

def print_config():
    """
    Print current configuration (for debugging)
    """
    config = get_config()
    print("Current ETCMon Configuration:")
    print("-" * 40)
    for key, value in config.items():
        # Don't print sensitive information
        if 'key' in key.lower() or 'password' in key.lower():
            print(f"{key}: {'*' * len(str(value))}")
        else:
            print(f"{key}: {value}")
    print("-" * 40)

if __name__ == "__main__":
    print_config()