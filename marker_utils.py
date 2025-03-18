import cv2
import numpy as np
import argparse
from pathlib import Path
import matplotlib.pyplot as plt

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

def visualize_markers(markers, output_dir=None, grid=True):
    """Visualize all markers, either in a grid or save individual images."""
    if grid:
        # Calculate grid dimensions
        n_markers = len(markers)
        grid_size = int(np.ceil(np.sqrt(n_markers)))
        
        # Create a grid of markers
        grid_img = np.ones((grid_size * 100, grid_size * 100), dtype=np.uint8) * 255
        
        idx = 0
        for marker_id, marker_array in sorted(markers.items()):
            if idx >= n_markers:
                break
                
            row = idx // grid_size
            col = idx % grid_size
            
            # Resize marker to fit in the grid
            marker_resized = cv2.resize(marker_array, (80, 80), interpolation=cv2.INTER_NEAREST)
            
            # Place marker in grid
            y_start = row * 100 + 10
            x_start = col * 100 + 10
            grid_img[y_start:y_start+80, x_start:x_start+80] = marker_resized
            
            # Add ID text
            cv2.putText(grid_img, f"ID: {marker_id}", 
                      (x_start, y_start + 95), 
                      cv2.FONT_HERSHEY_SIMPLEX, 
                      0.4, 0, 1)
            
            idx += 1
        
        # Display grid
        plt.figure(figsize=(12, 12))
        plt.imshow(grid_img, cmap='gray')
        plt.title(f"All {n_markers} ArUco Markers")
        plt.axis('off')
        
        if output_dir:
            output_path = Path(output_dir) / "all_markers.png"
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"Saved grid image to {output_path}")
        
        plt.show()
    
    elif output_dir:
        # Create output directory if it doesn't exist
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True, parents=True)
        
        # Save individual marker images
        for marker_id, marker_array in sorted(markers.items()):
            # Resize for better visibility
            marker_resized = cv2.resize(marker_array, (400, 400), interpolation=cv2.INTER_NEAREST)
            
            # Save image
            output_path = output_dir / f"marker_{marker_id:02d}.png"
            cv2.imwrite(str(output_path), marker_resized)
        
        print(f"Saved {len(markers)} individual marker images to {output_dir}")

def export_printable_markers(markers, output_file, page_size=(2100, 2970), marker_size=400, margin=50):
    """Create a PDF-ready image with multiple markers for printing."""
    # A4 page size in pixels at 300 DPI
    width, height = page_size
    
    # Calculate how many markers per row and column
    n_cols = (width - 2*margin) // (marker_size + margin)
    n_rows = (height - 2*margin) // (marker_size + margin)
    markers_per_page = n_rows * n_cols
    
    # Calculate total pages needed
    n_markers = len(markers)
    n_pages = int(np.ceil(n_markers / markers_per_page))
    
    print(f"Creating {n_pages} pages with {n_rows}x{n_cols} markers per page")
    
    # Create and save each page
    page_num = 1
    marker_idx = 0
    
    while marker_idx < n_markers:
        # Create a blank white page
        page = np.ones((height, width), dtype=np.uint8) * 255
        
        # Add markers to the page
        for row in range(n_rows):
            if marker_idx >= n_markers:
                break
                
            for col in range(n_cols):
                if marker_idx >= n_markers:
                    break
                
                # Get current marker ID and array
                marker_id = sorted(markers.keys())[marker_idx]
                marker_array = markers[marker_id]
                
                # Resize marker
                marker_resized = cv2.resize(marker_array, (marker_size, marker_size), interpolation=cv2.INTER_NEAREST)
                
                # Calculate position
                x_start = margin + col * (marker_size + margin)
                y_start = margin + row * (marker_size + margin)
                
                # Place marker on page
                page[y_start:y_start+marker_size, x_start:x_start+marker_size] = marker_resized
                
                # Add ID text
                cv2.putText(page, f"ID: {marker_id}", 
                          (x_start, y_start + marker_size + 20), 
                          cv2.FONT_HERSHEY_SIMPLEX, 
                          0.8, 0, 2)
                
                marker_idx += 1
        
        # Save the page
        output_path = f"{output_file}_page{page_num:02d}.png"
        cv2.imwrite(output_path, page)
        print(f"Saved page {page_num} to {output_path}")
        
        page_num += 1

def generate_proper_aruco_images(markers, output_dir):
    """Generate standard ArUco-formatted images from the custom marker data."""
    # Create output directory if it doesn't exist
    output_dir = Path(output_dir) / "aruco_formatted"
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Create a predefined dictionary as base
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
    
    # Replace entries with our custom markers and save images
    for marker_id, marker_array in sorted(markers.items()):
        if marker_id < 250:  # Maximum size of the dictionary
            # Extract the inner 6x6 grid (removing the border)
            inner_marker = marker_array[1:7, 1:7]
            
            # For proper ArUco format: white (255) should be 0, black (0) should be 1
            inner_marker_bin = np.zeros((6, 6), dtype=np.uint8)
            for i in range(6):
                for j in range(6):
                    # Convert the image values to binary format expected by ArUco
                    inner_marker_bin[i, j] = 0 if inner_marker[i, j] == 255 else 1
            
            # Update dictionary with this marker
            bytes_marker = cv2.aruco.Dictionary.getByteListFromBits(inner_marker_bin)
            dictionary.bytesList[marker_id] = bytes_marker
            
            # Generate proper ArUco marker image
            marker_size = 400  # Output size in pixels
            aruco_img = cv2.aruco.generateImageMarker(dictionary, marker_id, marker_size)
            
            # Save the image
            output_path = output_dir / f"aruco_marker_{marker_id:02d}.png"
            cv2.imwrite(str(output_path), aruco_img)
    
    print(f"Generated {len(markers)} ArUco-formatted marker images in {output_dir}")

def main():
    parser = argparse.ArgumentParser(description='Utilities for ArUco markers')
    parser.add_argument('--markers', type=str, default='markers.txt',
                        help='Path to the markers.txt file')
    parser.add_argument('--output-dir', type=str, default='markers',
                        help='Directory to save marker images')
    parser.add_argument('--visualize', action='store_true',
                        help='Visualize markers in a grid')
    parser.add_argument('--export', action='store_true',
                        help='Export printable marker pages')
    parser.add_argument('--export-file', type=str, default='printable_markers',
                        help='Base filename for printable marker pages')
    parser.add_argument('--generate-aruco', action='store_true',
                        help='Generate proper ArUco formatted markers')
    
    args = parser.parse_args()
    
    # Load markers
    markers_path = Path(args.markers)
    if not markers_path.exists():
        print(f"Error: Markers file '{args.markers}' not found.")
        return
    
    print(f"Loading markers from {markers_path}...")
    markers = load_custom_markers(markers_path)
    print(f"Loaded {len(markers)} markers.")
    
    # Generate proper ArUco markers
    if args.generate_aruco:
        generate_proper_aruco_images(markers, args.output_dir)
    
    # Visualize markers
    if args.visualize:
        visualize_markers(markers, args.output_dir)
    
    # Export printable markers
    if args.export:
        export_printable_markers(markers, args.export_file)
    
    # If no action specified, save individual marker images
    if not (args.visualize or args.export or args.generate_aruco):
        visualize_markers(markers, args.output_dir, grid=False)

if __name__ == "__main__":
    main() 