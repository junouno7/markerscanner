from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.uix.treeview import TreeView, TreeViewNode
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window

import cv2
import numpy as np
from pathlib import Path
import time
import os

# Import marker detection functions from existing modules
from marker_utils import load_custom_markers

class MarkerScannerApp(App):
    def build(self):
        # Main layout
        self.layout = BoxLayout(orientation='vertical')
        
        # Top control panel
        control_panel = BoxLayout(size_hint=(1, 0.1))
        
        # Camera selector
        self.camera_spinner = Spinner(
            text='Camera 0',
            values=('Camera 0', 'Camera 1', 'Camera 2'),
            size_hint=(0.2, 1)
        )
        control_panel.add_widget(self.camera_spinner)
        
        # Start/Stop button
        self.btn_start_stop = Button(text='Start', size_hint=(0.2, 1))
        self.btn_start_stop.bind(on_press=self.toggle_camera)
        control_panel.add_widget(self.btn_start_stop)
        
        # Snapshot button
        self.btn_snapshot = Button(text='Take Snapshot', size_hint=(0.2, 1))
        self.btn_snapshot.bind(on_press=self.take_snapshot)
        control_panel.add_widget(self.btn_snapshot)
        
        # Status label
        self.status_label = Label(text='Ready', size_hint=(0.4, 1))
        control_panel.add_widget(self.status_label)
        
        self.layout.add_widget(control_panel)
        
        # Camera preview
        self.image = Image(size_hint=(1, 0.7))
        self.layout.add_widget(self.image)
        
        # Marker info panel
        info_panel = BoxLayout(size_hint=(1, 0.2))
        
        # Detected markers list
        self.marker_list = Label(text='No markers detected', halign='left', valign='top')
        self.marker_list.bind(size=self.marker_list.setter('text_size'))
        info_panel.add_widget(self.marker_list)
        
        self.layout.add_widget(info_panel)
        
        # Initialize variables
        self.capture = None
        self.is_running = False
        self.markers_file = 'markers.txt'
        self.detected_markers = {}
        self.marker_timeout = 5
        
        # Load markers
        self.load_markers()
        
        return self.layout
    
    def load_markers(self):
        """Load markers and create dictionary."""
        try:
            markers_path = Path(self.markers_file)
            if not markers_path.exists():
                self.status_label.text = f"Error: Markers file not found"
                return
            
            self.status_label.text = "Loading markers..."
            self.markers = load_custom_markers(markers_path)
            self.status_label.text = f"Loaded {len(self.markers)} markers"
            
            # Create custom dictionary
            self.dictionary = self.create_custom_dictionary(self.markers)
            
            # Set detection parameters
            self.parameters = cv2.aruco.DetectorParameters()
            
        except Exception as e:
            self.status_label.text = f"Error: {str(e)}"
    
    def create_custom_dictionary(self, markers):
        """Create a custom ArUco dictionary from loaded markers."""
        # Create a predefined dictionary as base
        dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
        
        # Replace the first len(markers) entries with our custom markers
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
    
    def toggle_camera(self, instance):
        if self.is_running:
            self.stop_camera()
        else:
            self.start_camera()
    
    def start_camera(self):
        """Start the camera capture."""
        try:
            camera_idx = int(self.camera_spinner.text.split(' ')[1])
            self.capture = cv2.VideoCapture(camera_idx)
            
            if not self.capture.isOpened():
                self.status_label.text = f"Error: Could not open camera {camera_idx}"
                return
            
            self.is_running = True
            self.btn_start_stop.text = 'Stop'
            self.status_label.text = f"Camera {camera_idx} started"
            
            # Schedule the frame updates
            self.update_event = Clock.schedule_interval(self.update_frame, 1.0/30.0)  # 30 FPS
        except Exception as e:
            self.status_label.text = f"Error: {str(e)}"
    
    def stop_camera(self):
        """Stop the camera capture."""
        if self.capture:
            Clock.unschedule(self.update_event)
            self.capture.release()
            self.capture = None
            self.is_running = False
            self.btn_start_stop.text = 'Start'
            self.status_label.text = "Camera stopped"
    
    def update_frame(self, dt):
        """Update the camera frame."""
        if self.capture and self.is_running:
            ret, frame = self.capture.read()
            if ret:
                # Detect markers
                corners, ids, rejected = self.detect_markers(frame)
                
                # Draw detected markers
                frame = self.draw_markers(frame, corners, ids)
                
                # Update detected markers list
                self.update_detected_markers(ids)
                
                # Convert to texture
                buf = cv2.flip(frame, 0)
                buf = cv2.flip(buf, 1)
                buf = cv2.cvtColor(buf, cv2.COLOR_BGR2RGB)
                image_texture = Texture.create(
                    size=(frame.shape[1], frame.shape[0]), colorfmt='rgb')
                image_texture.blit_buffer(buf.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
                
                # Display the frame
                self.image.texture = image_texture
    
    def detect_markers(self, frame):
        """Detect ArUco markers in a frame."""
        detector = cv2.aruco.ArucoDetector(self.dictionary, self.parameters)
        corners, ids, rejected = detector.detectMarkers(frame)
        return corners, ids, rejected
    
    def draw_markers(self, frame, corners, ids):
        """Draw detected markers on frame."""
        if ids is not None:
            # Draw marker borders
            frame_with_markers = cv2.aruco.drawDetectedMarkers(frame.copy(), corners, None)
            
            # Add text for each marker
            for i, corner in enumerate(corners):
                corner_points = corner.reshape(4, 2).astype(np.int32)
                center_x = int(np.mean(corner_points[:, 0]))
                center_y = int(np.mean(corner_points[:, 1]))
                cv2.putText(frame_with_markers, f"ID: {ids[i][0]}", 
                            (center_x, center_y), 
                            cv2.FONT_HERSHEY_SIMPLEX, 
                            1.2, (0, 255, 0), 3)
            
            return frame_with_markers
        
        return frame
    
    def update_detected_markers(self, ids):
        """Update the list of detected markers with timestamps."""
        current_time = time.time()
        
        # Add newly detected markers
        if ids is not None:
            for id_item in ids:
                marker_id = id_item[0]
                self.detected_markers[marker_id] = current_time
        
        # Remove old markers
        markers_to_remove = []
        for marker_id, timestamp in self.detected_markers.items():
            if current_time - timestamp > self.marker_timeout:
                markers_to_remove.append(marker_id)
        
        for marker_id in markers_to_remove:
            del self.detected_markers[marker_id]
        
        # Update the marker list display
        if self.detected_markers:
            marker_text = "Detected markers:\n"
            for marker_id in sorted(self.detected_markers.keys()):
                marker_text += f"ID: {marker_id}\n"
            self.marker_list.text = marker_text
        else:
            self.marker_list.text = "No markers detected"
    
    def take_snapshot(self, instance):
        """Capture and save a snapshot."""
        if self.capture and self.is_running and hasattr(self, 'image') and self.image.texture:
            # Create snapshots directory if it doesn't exist
            snapshots_dir = Path("snapshots")
            snapshots_dir.mkdir(exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filepath = snapshots_dir / f"snapshot_{timestamp}.jpg"
            
            # Get current frame
            ret, frame = self.capture.read()
            if ret:
                # Detect markers
                corners, ids, rejected = self.detect_markers(frame)
                
                # Draw detected markers
                frame = self.draw_markers(frame, corners, ids)
                
                # Save the image
                cv2.imwrite(str(filepath), frame)
                self.status_label.text = f"Snapshot saved: {filepath}"
            else:
                self.status_label.text = "Failed to capture snapshot"
        else:
            self.status_label.text = "Camera not running"
    
    def on_stop(self):
        """Clean up resources when the app is closed."""
        self.stop_camera()

if __name__ == "__main__":
    MarkerScannerApp().run() 