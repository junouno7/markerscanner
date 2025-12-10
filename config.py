# Configuration settings for the Marker Scanner Web App
import cv2
import os

# Server settings
SERVER = {
    'host': '0.0.0.0',  # Listen on all interfaces
    'port': int(os.environ.get('PORT', 5000)),  # Use PORT environment variable or default to 5000
    'debug': False,  # Debug should be disabled in production
    'secret_key': os.environ.get('SECRET_KEY', '1234')  # Use environment variable for security
}

# Marker settings
MARKERS = {
    'file': os.environ.get('MARKERS_FILE', 'markers.txt'),  # Path to markers file
    'default_dictionary': cv2.aruco.DICT_6X6_250  # Fallback dictionary if custom markers fail
}

# Processing settings
PROCESSING = {
    'frame_quality': float(os.environ.get('FRAME_QUALITY', 0.5)),   # JPEG quality (lower = smaller payload, faster)
    'max_width': int(os.environ.get('MAX_WIDTH', 640)),       # Keep original width
    'max_height': int(os.environ.get('MAX_HEIGHT', 480)),     # Keep original height
    'process_every_n_ms': int(os.environ.get('PROCESS_RATE', 33))  # Process frames more frequently (20 -> 33)
}

# Advanced options
ADVANCED = {
    'cors_allowed_origins': os.environ.get('CORS_ORIGINS', '*'),  # CORS settings for socketio
    'marker_timeout_seconds': int(os.environ.get('MARKER_TIMEOUT', 120))   # How long to display markers after last detection
}

# Try to load local settings if available
try:
    from local_config import *
except ImportError:
    pass 