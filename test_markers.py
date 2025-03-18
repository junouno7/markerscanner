import cv2
import numpy as np
from pathlib import Path

# Create a basic marker for testing
def create_test_marker():
    # Create a simple test image with a marker
    img = np.ones((500, 500, 3), dtype=np.uint8) * 255
    
    # Draw a standard ArUco marker for testing (DICT_4X4_50 contains common markers)
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    marker_id = 0
    marker_size = 300
    marker_img = cv2.aruco.generateImageMarker(dictionary, marker_id, marker_size)
    
    # Place the marker in the center of the image
    h, w = marker_img.shape
    x_offset = (img.shape[1] - w) // 2
    y_offset = (img.shape[0] - h) // 2
    
    # Convert to 3 channels
    img[y_offset:y_offset+h, x_offset:x_offset+w, 0] = marker_img
    img[y_offset:y_offset+h, x_offset:x_offset+w, 1] = marker_img
    img[y_offset:y_offset+h, x_offset:x_offset+w, 2] = marker_img
    
    # Display and save the marker
    cv2.imshow("Test Marker", img)
    cv2.imwrite("test_marker.jpg", img)
    cv2.waitKey(1000)
    
    print("Created test marker image at test_marker.jpg")
    return img

# Test detection with a standard ArUco marker
def test_standard_marker():
    img = create_test_marker()
    
    # Create a standard dictionary
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    parameters = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(dictionary, parameters)
    
    # Detect markers
    corners, ids, rejected = detector.detectMarkers(img)
    
    # Draw results
    if ids is not None:
        print(f"Standard marker test: PASSED - Found {len(ids)} markers: {ids.flatten()}")
        # Use standalone function for drawing
        img_markers = cv2.aruco.drawDetectedMarkers(img.copy(), corners, ids)
        cv2.imshow("Detected Standard Markers", img_markers)
        cv2.waitKey(0)
    else:
        print("Standard marker test: FAILED - No markers detected")
    
    cv2.destroyAllWindows()

# Test your camera with standard markers
def test_camera_detection():
    # Use a standard dictionary that's known to work
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    parameters = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(dictionary, parameters)
    
    # Start video capture
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    print("Testing camera with standard ArUco dictionary. Press 'q' to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame")
            break
        
        # Detect markers
        corners, ids, rejected = detector.detectMarkers(frame)
        
        # Draw markers
        if ids is not None:
            frame = cv2.aruco.drawDetectedMarkers(frame.copy(), corners, ids)
            print(f"Found standard markers: {ids.flatten()}")
        
        # Display the result
        cv2.imshow('Camera Test', frame)
        
        # Exit on 'q' press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release resources
    cap.release()
    cv2.destroyAllWindows()

# Test your custom marker (from markers.txt)
def test_marker_24():
    from marker_scanner import load_custom_markers
    
    # Load markers from file
    try:
        markers = load_custom_markers("markers.txt")
    except Exception as e:
        print(f"Error loading markers: {e}")
        return
    
    if 24 not in markers:
        print("Marker 24 not found in markers.txt")
        return
    
    # Show marker 24
    marker_img = markers[24]
    cv2.imshow("Marker 24", cv2.resize(marker_img, (400, 400)))
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    print("Displayed marker 24. Make sure it looks correct (clean black and white pattern)")

if __name__ == "__main__":
    print("Testing standard ArUco marker detection")
    test_standard_marker()
    
    print("\nDo you want to test camera detection? (y/n)")
    if input().lower() == "y":
        test_camera_detection()
    
    print("\nDo you want to view marker 24? (y/n)")
    if input().lower() == "y":
        test_marker_24()