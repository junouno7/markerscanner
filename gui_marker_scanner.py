import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import threading
import time
from pathlib import Path
import argparse
import sys

class MarkerScannerApp:
    def __init__(self, root, markers_file='markers.txt'):
        self.root = root
        self.root.title("ArUco Marker Scanner")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        # Initialize variables
        self.markers_file = markers_file
        self.camera_index = 0
        self.is_running = False
        self.capture = None
        self.dictionary = None
        self.parameters = None
        self.detected_markers = {}  # Store detected markers with timestamp
        self.marker_timeout = 5  # How long markers remain "detected" in seconds
        
        # Create GUI
        self.create_widgets()
        
        # Load markers
        self.load_markers()
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top control panel
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Camera selection
        ttk.Label(control_frame, text="Camera:").pack(side=tk.LEFT, padx=(0, 5))
        self.camera_var = tk.StringVar(value=str(self.camera_index))
        camera_entry = ttk.Entry(control_frame, textvariable=self.camera_var, width=5)
        camera_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # Start/Stop button
        self.start_stop_button = ttk.Button(control_frame, text="Start", command=self.toggle_camera)
        self.start_stop_button.pack(side=tk.LEFT, padx=5)
        
        # Snapshot button
        self.snapshot_button = ttk.Button(control_frame, text="Take Snapshot", command=self.take_snapshot)
        self.snapshot_button.pack(side=tk.LEFT, padx=5)
        self.snapshot_button.config(state=tk.DISABLED)
        
        # Status indicator
        ttk.Label(control_frame, text="Status:").pack(side=tk.LEFT, padx=(20, 5))
        self.status_var = tk.StringVar(value="Idle")
        status_label = ttk.Label(control_frame, textvariable=self.status_var, foreground="blue")
        status_label.pack(side=tk.LEFT)
        
        # Split view: Video feed and marker list
        split_frame = ttk.Frame(main_frame)
        split_frame.pack(fill=tk.BOTH, expand=True)
        
        # Video feed on the left
        video_frame = ttk.LabelFrame(split_frame, text="Camera Feed")
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.video_label = ttk.Label(video_frame)
        self.video_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Detected markers on the right - fixed width issue by creating a frame with width
        markers_frame_container = ttk.Frame(split_frame, width=200)
        markers_frame_container.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        markers_frame_container.pack_propagate(False)  # Prevent the frame from shrinking
        
        # Detected markers frame inside the container
        markers_frame = ttk.LabelFrame(markers_frame_container, text="Detected Markers")
        markers_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a treeview for markers
        self.markers_tree = ttk.Treeview(markers_frame, columns=("ID", "Last Seen"), show="headings")
        self.markers_tree.heading("ID", text="Marker ID")
        self.markers_tree.heading("Last Seen", text="Last Seen")
        self.markers_tree.column("ID", width=80)
        self.markers_tree.column("Last Seen", width=120)
        self.markers_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Status bar at the bottom
        status_bar = ttk.Frame(main_frame)
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
        self.marker_count_var = tk.StringVar(value="No markers detected")
        ttk.Label(status_bar, textvariable=self.marker_count_var).pack(side=tk.LEFT)
    
    def load_markers(self):
        """Load custom markers from file and create ArUco dictionary."""
        try:
            # Check if file exists
            markers_path = Path(self.markers_file)
            if not markers_path.exists():
                messagebox.showerror("Error", f"Markers file '{self.markers_file}' not found.")
                self.root.quit()
                return
            
            self.status_var.set("Loading markers...")
            
            # Load markers
            markers = self.load_custom_markers(markers_path)
            
            if not markers:
                messagebox.showerror("Error", "No valid markers found in the file.")
                self.root.quit()
                return
            
            # Create dictionary
            self.dictionary = self.create_custom_dictionary(markers)
            
            # Create parameters
            self.parameters = cv2.aruco.DetectorParameters()
            
            self.status_var.set(f"Loaded {len(markers)} markers")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load markers: {str(e)}")
            self.root.quit()
    
    def load_custom_markers(self, markers_file):
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
    
    def toggle_camera(self):
        """Start or stop the camera feed."""
        if self.is_running:
            self.stop_camera()
        else:
            self.start_camera()
    
    def start_camera(self):
        """Start the camera feed."""
        try:
            # Get camera index from input
            try:
                self.camera_index = int(self.camera_var.get())
            except ValueError:
                messagebox.showerror("Error", "Camera index must be a number")
                return
            
            # Open camera
            self.capture = cv2.VideoCapture(self.camera_index)
            
            if not self.capture.isOpened():
                messagebox.showerror("Error", f"Could not open camera {self.camera_index}")
                return
            
            # Start video thread
            self.is_running = True
            self.video_thread = threading.Thread(target=self.update_frame, daemon=True)
            self.video_thread.start()
            
            # Update UI
            self.start_stop_button.config(text="Stop")
            self.snapshot_button.config(state=tk.NORMAL)
            self.status_var.set("Running")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start camera: {str(e)}")
    
    def stop_camera(self):
        """Stop the camera feed."""
        self.is_running = False
        if self.capture is not None:
            self.capture.release()
            self.capture = None
        
        # Update UI
        self.start_stop_button.config(text="Start")
        self.snapshot_button.config(state=tk.DISABLED)
        self.status_var.set("Stopped")
    
    def update_frame(self):
        """Update the video frame continuously."""
        while self.is_running:
            try:
                ret, frame = self.capture.read()
                if not ret:
                    # Try to reconnect
                    time.sleep(0.1)
                    continue
                
                # Detect markers
                corners, ids, rejected = self.detect_markers(frame)
                
                # Update detected markers list
                self.update_detected_markers(ids)
                
                # Draw markers on frame
                frame = self.draw_markers(frame, corners, ids)
                
                # Convert to PhotoImage and display
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, _ = rgb_frame.shape
                
                # Resize to fit the window (preserving aspect ratio)
                max_w, max_h = 640, 480
                if w > max_w or h > max_h:
                    ratio = min(max_w / w, max_h / h)
                    new_w = int(w * ratio)
                    new_h = int(h * ratio)
                    rgb_frame = cv2.resize(rgb_frame, (new_w, new_h))
                
                pil_img = Image.fromarray(rgb_frame)
                photo_img = ImageTk.PhotoImage(image=pil_img)
                
                # Update UI (thread-safe)
                self.root.after(0, self.update_ui, photo_img)
                
            except Exception as e:
                print(f"Error in video loop: {str(e)}")
                time.sleep(0.1)
    
    def update_ui(self, photo_img):
        """Update UI elements (called from the main thread)."""
        self.video_label.configure(image=photo_img)
        self.video_label.image = photo_img  # Keep a reference
        
        # Update status
        count = len(self.detected_markers)
        self.marker_count_var.set(f"Detected markers: {count}")
    
    def detect_markers(self, frame):
        """Detect ArUco markers in the frame."""
        if self.dictionary is None:
            return [], None, []
        
        # Create detector with the dictionary
        detector = cv2.aruco.ArucoDetector(self.dictionary, self.parameters)
        # Detect markers
        corners, ids, rejected = detector.detectMarkers(frame)
        return corners, ids, rejected
    
    def draw_markers(self, frame, corners, ids):
        """Draw detected markers on the frame."""
        if ids is not None:
            # Use the standalone function but pass None instead of ids to only draw borders
            frame_with_markers = cv2.aruco.drawDetectedMarkers(frame.copy(), corners, None)
            
            # Add text for each marker with larger font size
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
        """Update the list of detected markers."""
        current_time = time.time()
        
        # Add new markers
        if ids is not None:
            for marker_id in ids.flatten():
                self.detected_markers[marker_id] = current_time
        
        # Remove expired markers
        expired_markers = []
        for marker_id, timestamp in self.detected_markers.items():
            if current_time - timestamp > self.marker_timeout:
                expired_markers.append(marker_id)
        
        for marker_id in expired_markers:
            del self.detected_markers[marker_id]
        
        # Update treeview
        self.root.after(0, self.update_markers_treeview)
    
    def update_markers_treeview(self):
        """Update the markers treeview with currently detected markers."""
        # Clear treeview
        for item in self.markers_tree.get_children():
            self.markers_tree.delete(item)
        
        # Add markers
        current_time = time.time()
        for marker_id, timestamp in sorted(self.detected_markers.items()):
            seconds_ago = int(current_time - timestamp)
            time_str = f"{seconds_ago}s ago" if seconds_ago > 0 else "just now"
            self.markers_tree.insert("", tk.END, values=(marker_id, time_str))
    
    def take_snapshot(self):
        """Take a snapshot of the current frame and save it."""
        if not self.is_running or self.capture is None:
            return
        
        try:
            ret, frame = self.capture.read()
            if not ret:
                messagebox.showerror("Error", "Failed to capture snapshot")
                return
            
            # Detect markers
            corners, ids, rejected = self.detect_markers(frame)
            
            # Draw markers on frame
            frame = self.draw_markers(frame, corners, ids)
            
            # Save the frame
            file_path = filedialog.asksaveasfilename(
                defaultextension=".jpg",
                filetypes=[("JPEG Image", "*.jpg"), ("PNG Image", "*.png"), ("All Files", "*.*")]
            )
            
            if file_path:
                cv2.imwrite(file_path, frame)
                messagebox.showinfo("Snapshot", f"Snapshot saved to {file_path}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save snapshot: {str(e)}")

def parse_args():
    parser = argparse.ArgumentParser(description='ArUco Marker Scanner GUI')
    parser.add_argument('--markers', type=str, default='markers.txt',
                        help='Path to the markers.txt file')
    return parser.parse_args()

def main():
    args = parse_args()
    
    root = tk.Tk()
    app = MarkerScannerApp(root, markers_file=args.markers)
    
    # Set icon and styling if available
    try:
        # Set theme if available
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass
    
    root.mainloop()

if __name__ == "__main__":
    main() 