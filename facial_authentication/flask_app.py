from flask import Flask, jsonify
import threading
import time
import socket
import datetime
import sys
import os

# Add the project root to Python path to import your modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your existing application
# from app_authentication import AuthenticationApplication
from modern_app_authentication import ModernAuthenticationApplication
import tkinter as tk
import src.logger.custom_logger as custom_logger

LOGGER = custom_logger.get_logger()

app = Flask(__name__)

# Global variables to track application state
authentication_app = None
app_thread = None
app_status = {
    'status': 'starting',
    'last_check': None,
    'station_id': None,
    'hostname': socket.gethostname(),
    'ip_address': socket.gethostbyname(socket.gethostname()),
    'uptime_start': datetime.datetime.now()
}

def run_authentication_app():
    """
    Run the main ETC authentication application in a separate thread
    """
    global authentication_app, app_status
    
    try:
        LOGGER.info("Starting ETC Authentication Application...")
        app_status['status'] = 'running'
        
        # Create and run the main application
        root = tk.Tk()
        #authentication_app = AuthenticationApplication(root)
        authentication_app = ModernAuthenticationApplication(root)
        authentication_app.pack(side="top", fill="both", expand=True)
        
        # Store station ID for monitoring
        app_status['station_id'] = authentication_app.station_id
        
        # Open web browser as in original main()
        import webbrowser
        webbrowser.open("http://localhost:8080/psms/mcs/ETC.xhtml?mode=facial&inout=O")
        
        LOGGER.info("ETC Authentication Application started successfully")
        root.mainloop()
        
    except Exception as e:
        LOGGER.error(f"Error running authentication app: {e}")
        app_status['status'] = 'error'
        app_status['error'] = str(e)

@app.route('/')
def run_etc_app():
    """
    Main endpoint to start/check the ETC application
    """
    global app_thread, app_status
    
    if app_thread is None or not app_thread.is_alive():
        # Start the authentication app in a separate thread
        app_thread = threading.Thread(target=run_authentication_app, daemon=True)
        app_thread.start()
        
        return jsonify({
            'status': 'started',
            'message': 'ETC Authentication Application is starting...',
            'station_id': app_status.get('station_id'),
            'timestamp': datetime.datetime.now().isoformat()
        })
    else:
        return jsonify({
            'status': 'already_running',
            'message': 'ETC Authentication Application is already running',
            'station_id': app_status.get('station_id'),
            'timestamp': datetime.datetime.now().isoformat()
        })

@app.route('/health')
def health_check():
    """
    Health endpoint for monitoring
    This should be reflected in your UI to show that the etcmon client is up and running
    """
    global authentication_app, app_thread, app_status
    
    # Update last check time
    app_status['last_check'] = datetime.datetime.now().isoformat()
    
    # Calculate uptime
    uptime = datetime.datetime.now() - app_status['uptime_start']
    uptime_seconds = int(uptime.total_seconds())
    
    # Check if main application thread is running
    main_app_running = app_thread is not None and app_thread.is_alive()
    
    # Determine overall health status
    if main_app_running and app_status['status'] == 'running':
        health_status = 'healthy'
        message = 'All services are running normally'
    elif app_status['status'] == 'error':
        health_status = 'unhealthy'
        message = f"Application error: {app_status.get('error', 'Unknown error')}"
    elif app_status['status'] == 'starting':
        health_status = 'starting'
        message = 'Application is starting up'
    else:
        health_status = 'unhealthy'
        message = 'Main application thread is not running'
    
    return jsonify({
        'status': 'ok',
        'health': health_status,
        'message': message,
        'details': {
            'station_id': app_status.get('station_id'),
            'hostname': app_status['hostname'],
            'ip_address': app_status['ip_address'],
            'main_app_running': main_app_running,
            'app_status': app_status['status'],
            'uptime_seconds': uptime_seconds,
            'uptime_human': str(uptime).split('.')[0],  # Remove microseconds
            'last_check': app_status['last_check'],
            'flask_server': 'running'
        },
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/status')
def detailed_status():
    """
    Detailed status endpoint with more information
    """
    return jsonify({
        'application': {
            'name': 'ETC Face Recognition System',
            'version': '1.0.0',
            'status': app_status['status']
        },
        'system': {
            'hostname': app_status['hostname'],
            'ip_address': app_status['ip_address'],
            'station_id': app_status.get('station_id')
        },
        'runtime': {
            'uptime_start': app_status['uptime_start'].isoformat(),
            'last_check': app_status['last_check'],
            'main_thread_alive': app_thread is not None and app_thread.is_alive() if app_thread else False
        },
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/restart')
def restart_app():
    """
    Endpoint to restart the main application
    """
    global app_thread, authentication_app, app_status
    
    try:
        # Stop existing application if running
        if authentication_app:
            authentication_app.quit_app()
        
        # Reset status
        app_status['status'] = 'restarting'
        
        # Start new instance
        app_thread = threading.Thread(target=run_authentication_app, daemon=True)
        app_thread.start()
        
        return jsonify({
            'status': 'success',
            'message': 'Application restart initiated',
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        LOGGER.error(f"Error restarting application: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to restart application: {str(e)}',
            'timestamp': datetime.datetime.now().isoformat()
        }), 500

# Auto-start ETC application after Flask server starts
def auto_start_etc_app():
    """Auto-start the ETC application after a delay"""
    import time
    import requests
    
    # Wait for Flask server to be ready
    time.sleep(2)
    
    try:
        # Trigger the ETC application startup
        response = requests.get('http://127.0.0.1:5000/', timeout=5)
        if response.status_code == 200:
            print(" ETC Application auto-started successfully!")
        else:
            print(f"⚠️ Auto-start failed with status: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Auto-start failed: {e}")

# Run the application
if __name__ == '__main__':
    LOGGER.info("Starting Flask monitoring server...")
    print("ETC Monitoring Server Starting...")
    print("Health endpoint available at: http://127.0.0.1:5000/health")
    print("Main application endpoint: http://127.0.0.1:5000/")
    print("Detailed status: http://127.0.0.1:5000/status")
    
    # Start auto-trigger in background thread
    import threading
    threading.Thread(target=auto_start_etc_app, daemon=True).start()
    
    # Start the Flask app
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)