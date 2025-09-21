# ArUco Marker Scanner

A real-time web application that detects and identifies ArUco markers through live camera feed using Flask, WebSocket, and OpenCV for computer vision processing. The app is designed to detect 50 custom + 200 dictionary 6x6 ArUco markers (with IDs 0-249) and display their ID numbers.

## Live site

Visit the live site [here](https://arucoscanner.onrender.com/)

## Demo

[![Demo Video](https://img.youtube.com/vi/jOH16TEf3Po/maxresdefault.jpg)](http://youtube.com/shorts/jOH16TEf3Po)

*Real-time ArUco marker detection demo*

## Requirements

- Python 3.6+
- OpenCV with ArUco module (via opencv-contrib-python)
- Numpy
- Matplotlib (for visualization)
- Pillow (for GUI version)

## Installation

1. Clone this repository or download the files
2. Install required packages:

```bash
pip install -r requirements.txt
```

## Usage

### CLI Marker Detection

To run the command-line marker detection app with your camera:

```bash
python marker_scanner.py
```

Options:
- `--markers`: Path to the markers.txt file (default: markers.txt)
- `--camera`: Camera index to use (default: 0)

Press 'q' to quit the application.

### GUI Marker Detection

For a more user-friendly interface, use the GUI version:

```bash
python gui_marker_scanner.py
```

The GUI version provides:
- Live camera feed with marker detection
- List of detected markers with timestamps
- Snapshot capability to save detection results
- Camera selection

Options:
- `--markers`: Path to the markers.txt file (default: markers.txt)

### Marker Utilities

The `marker_utils.py` script can be used to visualize and export the markers:

```bash
# Generate individual marker images
python marker_utils.py

# Visualize all markers in a grid
python marker_utils.py --visualize

# Export printable marker pages
python marker_utils.py --export
```

Options:
- `--markers`: Path to the markers.txt file (default: markers.txt)
- `--output-dir`: Directory to save marker images (default: markers)
- `--visualize`: Visualize markers in a grid
- `--export`: Export printable marker pages
- `--export-file`: Base filename for printable marker pages (default: printable_markers)

## Marker Information

The markers are 6x6 ArUco markers (8x8 including black border) intended to be printed at 15cm x 15cm physical size. The marker data is stored in `markers.txt`.

Tags: Aruco, Marker, Scanner, App, OpenCV, Python
