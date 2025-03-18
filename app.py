import os
import cv2
import numpy as np
from flask import Flask, render_template, Response, jsonify
from flask_socketio import SocketIO, emit
import base64
import json
from pathlib import Path
import time
from threading import Lock

# Import our marker detection functions
from marker_scanner import load_custom_markers, create_custom_dictionary, detect_markers, draw_markers

# Import configuration
from config import SERVER, MARKERS, PROCESSING, ADVANCED

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', SERVER['secret_key'])
socketio = SocketIO(app, cors_allowed_origins=ADVANCED['cors_allowed_origins'])

# Load markers and create dictionary
print("Loading markers...")
markers_path = Path(MARKERS['file'])
if not markers_path.exists():
    print(f"Error: Markers file '{MARKERS['file']}' not found.")
    # Use a predefined dictionary as fallback
    dictionary = cv2.aruco.getPredefinedDictionary(MARKERS['default_dictionary'])
else:
    markers = load_custom_markers(markers_path)
    print(f"Loaded {len(markers)} markers.")
    dictionary = create_custom_dictionary(markers)

# Set detection parameters
parameters = cv2.aruco.DetectorParameters()

# Thread lock for thread safety
thread_lock = Lock()

@app.route('/')
def index():
    """Serve the index page"""
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    
    # Send configuration to client
    config = {
        'processing': {
            'process_every_n_ms': PROCESSING['process_every_n_ms'],
            'frame_quality': PROCESSING['frame_quality']
        },
        'advanced': {
            'marker_timeout_seconds': ADVANCED['marker_timeout_seconds']
        }
    }
    
    emit('status', {
        'message': 'Connected to server',
        'config': config
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

@socketio.on('frame')
def handle_frame(data):
    """
    Process a frame from the client
    data: Dict containing base64 encoded image
    """
    # Decode the image
    try:
        # Get the base64 image data
        image_data = data['image'].split(',')[1]
        image_bytes = base64.b64decode(image_data)
        
        # Convert to OpenCV format
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Resize if needed
        h, w = frame.shape[:2]
        if w > PROCESSING['max_width'] or h > PROCESSING['max_height']:
            scale = min(PROCESSING['max_width'] / w, PROCESSING['max_height'] / h)
            frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
        
        # Process the frame for markers
        corners, ids, rejected = detect_markers(frame, dictionary, parameters)
        
        # Draw on the frame
        processed_frame = draw_markers(frame, corners, ids)
        
        # Convert back to base64 for sending to client
        _, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, int(PROCESSING['frame_quality'] * 100)])
        processed_image = base64.b64encode(buffer).decode('utf-8')
        
        # Generate marker data
        marker_data = []
        if ids is not None:
            for i, marker_id in enumerate(ids):
                marker_data.append({
                    'id': int(marker_id[0]),
                    'timestamp': time.time()
                })
        
        # Send the processed image and marker data back to the client
        emit('processed_frame', {
            'image': f'data:image/jpeg;base64,{processed_image}',
            'markers': marker_data
        })
    
    except Exception as e:
        print(f"Error processing frame: {str(e)}")
        emit('error', {'message': f'Error processing frame: {str(e)}'})

if __name__ == '__main__':
    # Start the server
    port = int(os.environ.get('PORT', SERVER['port']))
    
    # Debug should be False in production
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    socketio.run(
        app, 
        host=SERVER['host'], 
        port=port, 
        debug=debug, 
        allow_unsafe_werkzeug=True
    ) 