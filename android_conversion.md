# Android Conversion Guide

This guide provides information on how to convert the ArUco Marker Scanner Python application to an Android APK.

## Option 1: Kivy with Buildozer

[Kivy](https://kivy.org/) is a Python framework for developing multi-touch applications that can be deployed to Android.

### Steps:

1. **Install Kivy and dependencies**:
   ```bash
   pip install kivy buildozer
   ```

2. **Create a Kivy version of the app**:
   - Create a `main.py` file that implements the UI using Kivy
   - Use the OpenCV functionality from the original app
   - Example structure:
   
   ```python
   from kivy.app import App
   from kivy.uix.boxlayout import BoxLayout
   from kivy.uix.button import Button
   from kivy.uix.label import Label
   from kivy.clock import Clock
   from kivy.graphics.texture import Texture
   from kivy.uix.image import Image
   import cv2
   import numpy as np
   # Import marker detection functions from marker_scanner.py
   
   class MarkerScannerApp(App):
       # Implement app here
   ```

3. **Create a buildozer.spec file**:
   ```bash
   buildozer init
   ```

4. **Modify buildozer.spec**:
   - Add opencv-contrib-python to requirements
   - Configure Android permissions

5. **Build the APK**:
   ```bash
   buildozer android debug
   ```

## Option 2: Chaquopy

[Chaquopy](https://chaquo.com/chaquopy/) is a tool for running Python code in Android applications.

### Steps:

1. **Set up an Android Studio project**

2. **Add Chaquopy to your project**:
   - Add the Chaquopy plugin to your `build.gradle` file
   - Configure Python package requirements including opencv-contrib-python

3. **Integrate the Python code**:
   - Copy the Python code into the project
   - Create a Java/Kotlin interface to call the Python code

4. **Create the Android UI**:
   - Create a camera preview
   - Display detection results
   - Handle user interactions

5. **Build and deploy**

## Option 3: OpenCV Android SDK

This approach involves rewriting the application natively in Java or Kotlin using the OpenCV Android SDK.

### Steps:

1. **Set up Android Studio project**

2. **Add OpenCV Android SDK**:
   - Download from [OpenCV Releases](https://opencv.org/releases/)
   - Add as a module to your project

3. **Port the core functionality**:
   - Implement custom ArUco marker dictionary creation
   - Set up camera handling and marker detection

4. **Create the Android UI**:
   - Camera preview
   - Detection results display

5. **Build and deploy**

## Recommended Approach

For this specific application, **Option 3** (OpenCV Android SDK) is recommended for the best performance and user experience. The ArUco detection functions are already available in the OpenCV Android SDK, making the implementation straightforward.

However, if you prefer to reuse most of your Python code, **Option 1** (Kivy) provides a more direct path to converting your existing code to Android.

## Resources

- [Kivy Documentation](https://kivy.org/doc/stable/)
- [Buildozer Documentation](https://buildozer.readthedocs.io/)
- [Chaquopy Documentation](https://chaquo.com/chaquopy/doc/)
- [OpenCV Android Documentation](https://docs.opencv.org/master/d0/d0c/tutorial_android_dev_intro.html)
- [ArUco Detection in OpenCV Java](https://docs.opencv.org/master/d5/dae/tutorial_aruco_detection.html) 