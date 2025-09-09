#!/usr/bin/env python3
"""
ETC Connection Monitoring Test Script

Run this script to test the ETC connection monitoring functionality.
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

try:
    from src.network_comms.etc_connection_monitor import ETCConnectionMonitor
    print(" ETCConnectionMonitor imported successfully")
except ImportError as e:
    print(f" Failed to import ETCConnectionMonitor: {e}")
    sys.exit(1)

def test_etc_monitoring():
    """Test ETC connection monitoring"""
    print("🔄 Starting ETC Connection Test...")
    print("-" * 50)
    
    # Create monitor
    monitor = ETCConnectionMonitor("http://localhost:8080")
    
    # Add callback to see status updates
    def status_callback(status_type, is_connected, details=None):
        status = " Connected" if is_connected else " Disconnected"
        print(f" {status_type.upper()}: {status}")
        if details:
            print(f"   Details: {details}")
    
    monitor.add_status_callback(status_callback)
    
    # Test immediate connection
    print(" Testing immediate connection...")
    status = monitor.test_connection_now()
    
    print("\n Connection Status Summary:")
    print(f"   ETC Web: {'' if status['etc_web_reachable'] else ''}")
    print(f"   WebSocket: {'' if status['websocket_reachable'] else ''}")
    print(f"   Overall: {status['overall_status']}")
    
    if status['last_check']:
        print(f"   Last Check: {status['last_check']}")
    
    # Start continuous monitoring
    print("\n🔄 Starting continuous monitoring for 30 seconds...")
    monitor.start_monitoring()
    
    try:
        time.sleep(30)
    except KeyboardInterrupt:
        print("\n Test interrupted by user")
    finally:
        monitor.stop_monitoring()
        print("\n Test completed")

if __name__ == "__main__":
    test_etc_monitoring()
