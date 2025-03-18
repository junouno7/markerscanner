import cv2
import numpy as np
import argparse
from pathlib import Path

def load_custom_markers(markers_file):
    """Load custom ArUco markers from a text file."""
    markers = {}
    
    with open(markers_file, 'r') as f:
        for line in f:
            # Skip comments and empty lines
            if line.startswith('#') or not line.strip():
                continue
                
            # Parse marker data
            parts = line.strip().split(': ')
            if len(parts) != 2:
                continue
                
            marker_id = int(parts[0])
            binary_rows = parts[1].split()
            
            # Convert binary representation to numpy array
            marker_array = np.zeros((8, 8), dtype=np.uint8)
            for i, row in enumerate(binary_rows):
                for j, bit in enumerate(row):
                    marker_array[i, j] = 255 if bit == '0' else 0
            
            markers[marker_id] = marker_array
            
    return markers

def create_custom_dictionary(markers):
    """Create a custom ArUco dictionary from loaded markers."""
    # Create a predefined dictionary as base
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
    
    # Replace the first len(markers) entries with our custom markersq
    for marker_id, marker_array in markers.items():
        if marker_id < 250:  # Maximum size of the dictionary
            # Extract the inner 6x6 grid (removing the border)
            inner_marker = marker_array[1:7, 1:7]
            
            # For proper ArUco format: white (255) should be 0, black (0) should be 1
            inner_marker_bin = np.zeros((6, 6), dtype=np.uint8)
            for i in range(6):
                for j in range(6):
                    # Convert the image values to binary format expected by ArUco
                    inner_marker_bin[i, j] = 0 if inner_marker[i, j] == 255 else 1
            
            # Get byte representation and update dictionary
            bytes_marker = cv2.aruco.Dictionary.getByteListFromBits(inner_marker_bin)
            dictionary.bytesList[marker_id] = bytes_marker
    
    return dictionary

def detect_markers(frame, dictionary, parameters):
    """Detect ArUco markers in a frame."""
    # Create detector with the dictionary
    detector = cv2.aruco.ArucoDetector(dictionary, parameters)
    # Detect markers
    corners, ids, rejected = detector.detectMarkers(frame)
    print(f"Detection result: {'No markers detected' if ids is None else f'Found {len(ids)} markers: {ids.flatten()}'}")
    return corners, ids, rejected

def draw_markers(frame, corners, ids):
    """Draw detected markers on frame."""
    if ids is not None:
        # Create a copy of the frame to draw on
        frame_with_markers = frame.copy()
        
        # Draw marker borders
        cv2.aruco.drawDetectedMarkers(frame_with_markers, corners, None)
        
        # Draw larger red squares at the top-left corner of each marker
        for corner in corners:
            corner_points = corner.reshape(4, 2).astype(np.int32)
            # Get the top-left corner (first point in the array)
            top_left = tuple(corner_points[0].astype(int))
            # Draw a larger square (adjust size as needed)
            square_size = 10  # Increase this for a larger square
            cv2.rectangle(frame_with_markers, 
                         (top_left[0] - square_size//2, top_left[1] - square_size//2),
                         (top_left[0] + square_size//2, top_left[1] + square_size//2),
                         (0, 0, 255),  # Red color
                         -1)  # Filled square
        
        # Add text for each marker with larger font size
        for i, corner in enumerate(corners):
            corner_points = corner.reshape(4, 2).astype(np.int32)
            
            # Calculate center X for horizontal alignment
            center_x = int(np.mean(corner_points[:, 0]))
            
            # Calculate bottom Y position (maximum Y value plus offset)
            bottom_y = int(np.max(corner_points[:, 1])) + 25  # px below the marker
            
            # Get the text to display and its size
            text = f"ID: {ids[i][0]}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 1.0
            thickness = 2
            (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)
            
            # Calculate position to center the text horizontally
            text_x = center_x - (text_width // 2)
            
            # Draw the text
            cv2.putText(frame_with_markers, text, 
                        (text_x, bottom_y), 
                        font, 
                        font_scale, (0, 255, 0), thickness)
        
        return frame_with_markers
    
    return frame

def main():
    parser = argparse.ArgumentParser(description='Detect custom ArUco markers')
    parser.add_argument('--markers', type=str, default='markers.txt',
                        help='Path to the markers.txt file')
    parser.add_argument('--camera', type=int, default=0,
                        help='Camera index (default: 0)')
    args = parser.parse_args()
    
    # Load markers
    markers_path = Path(args.markers)
    if not markers_path.exists():
        print(f"Error: Markers file '{args.markers}' not found.")
        return
    
    print(f"Loading markers from {markers_path}...")
    markers = load_custom_markers(markers_path)
    print(f"Loaded {len(markers)} markers.")
    
    # Create custom dictionary
    dictionary = create_custom_dictionary(markers)
    
    # Set detection parameters
    parameters = cv2.aruco.DetectorParameters()
    
    # Start video capture
    cap = cv2.VideoCapture(args.camera)
    
    if not cap.isOpened():
        print(f"Error: Could not open camera {args.camera}")
        return
    
    print("Press 'q' to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame")
            break
        
        # Detect markers
        corners, ids, rejected = detect_markers(frame, dictionary, parameters)
        
        # Draw detected markers
        frame = draw_markers(frame, corners, ids)
        
        # Display the result
        cv2.imshow('Marker Scanner', frame)
        
        # Exit on 'q' press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release resources
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main() 