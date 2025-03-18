document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const cameraFeed = document.getElementById('cameraFeed');
    const captureCanvas = document.getElementById('captureCanvas');
    const processedImage = document.getElementById('processedImage');
    const startCameraBtn = document.getElementById('startCamera');
    const stopCameraBtn = document.getElementById('stopCamera');
    const cameraSelect = document.getElementById('cameraSelect');
    const markerList = document.getElementById('markerList');
    const statusMessage = document.getElementById('statusMessage');

    // Global variables
    let stream = null;
    let socket = null;
    let isProcessing = false;
    let processingInterval = null;
    const captureContext = captureCanvas.getContext('2d');
    const detectedMarkers = {};
    let zoomLevel = 1.0; // Current zoom level
    let maxZoom = 10.0;  // Default max zoom (will be updated if available)
    let minZoom = 1.0;   // Default min zoom
    let videoTrack = null; // Current video track for zoom control
    
    // Processing settings - these should match server settings
    const PROCESSING = {
        processEveryMs: 33,  // Process frames every 33ms by default
        markerTimeoutSeconds: 30  // How long to keep markers visible
    };

    // Initialize the app
    initializeApp();

    function initializeApp() {
        // Connect to Socket.IO server
        socket = io();

        // Event listeners for socket connection
        socket.on('connect', () => {
            updateStatus('Connected to server');
        });

        socket.on('disconnect', () => {
            updateStatus('Disconnected from server');
        });

        socket.on('status', (data) => {
            updateStatus(data.message);
            
            // Check if server sent configuration
            if (data.config) {
                if (data.config.processing) {
                    PROCESSING.processEveryMs = data.config.processing.process_every_n_ms || PROCESSING.processEveryMs;
                    PROCESSING.markerTimeoutSeconds = data.config.advanced.marker_timeout_seconds || PROCESSING.markerTimeoutSeconds;
                }
            }
        });

        socket.on('error', (data) => {
            updateStatus(`Error: ${data.message}`, true);
        });

        socket.on('processed_frame', (data) => {
            // Display processed image
            processedImage.src = data.image;
            isProcessing = false;

            // Update marker list
            updateMarkerList(data.markers);
        });

        // Camera button event listeners
        startCameraBtn.addEventListener('click', startCamera);
        stopCameraBtn.addEventListener('click', stopCamera);

        // Camera selection event listener
        cameraSelect.addEventListener('change', () => {
            if (stream) {
                stopCamera();
                startCamera();
            }
        });

        // Populate camera list
        populateCameraList();
    }

    async function populateCameraList() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const videoDevices = devices.filter(device => device.kind === 'videoinput');
            
            // Clear select options
            cameraSelect.innerHTML = '';
            
            // Add default option
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.text = 'Select Camera';
            cameraSelect.appendChild(defaultOption);
            
            // Add camera options
            videoDevices.forEach((device, index) => {
                const option = document.createElement('option');
                option.value = device.deviceId;
                option.text = device.label || `Camera ${index + 1}`;
                cameraSelect.appendChild(option);
            });

            // If only one camera, select it
            if (videoDevices.length === 1) {
                cameraSelect.value = videoDevices[0].deviceId;
            }
        } catch (error) {
            updateStatus(`Error enumerating devices: ${error.message}`, true);
        }
    }

    async function startCamera() {
        try {
            // Camera constraints
            const constraints = {
                video: {
                    facingMode: 'environment', // Use back camera if available
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    zoom: 1.0 // Initial zoom level
                }
            };

            // If a specific camera is selected, use it
            if (cameraSelect.value) {
                constraints.video = {
                    deviceId: { exact: cameraSelect.value },
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    zoom: 1.0 // Initial zoom level
                };
            }

            // Get user media
            stream = await navigator.mediaDevices.getUserMedia(constraints);
            cameraFeed.srcObject = stream;
            
            // Get the video track for controlling zoom
            videoTrack = stream.getVideoTracks()[0];
            
            // Get the capabilities of the camera
            const capabilities = videoTrack.getCapabilities();
            
            // Check if zoom is supported
            if (capabilities.zoom) {
                minZoom = capabilities.zoom.min;
                maxZoom = capabilities.zoom.max;
                zoomLevel = minZoom;
                updateStatus(`Camera Live - Zoom Available (${minZoom}x-${maxZoom.toFixed(1)}x)`);
                // Initialize zoom controls
                initZoomControls();
            } else {
                updateStatus('Camera Live - Zoom not available on this device');
            }
            
            // Set canvas size to match video
            captureCanvas.width = 640;
            captureCanvas.height = 480;

            // Update UI
            startCameraBtn.disabled = true;
            stopCameraBtn.disabled = false;
            updateStatus('Camera started', false);

            // Start processing
            startFrameProcessing();
        } catch (error) {
            updateStatus(`Error starting camera: ${error.message}`, true);
        }
    }

    function stopCamera() {
        if (stream) {
            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());
            stream = null;
            cameraFeed.srcObject = null;
            
            // Clear the processing interval
            if (processingInterval) {
                clearInterval(processingInterval);
                processingInterval = null;
            }
            
            // Clean up video feed and reset zoom controls
            videoTrack = null;
            zoomLevel = 1.0;
            
            // Reset processed image to black
            processedImage.removeAttribute('src');
            
            // Clear any existing zoom indicators and reset buttons
            const existingIndicator = document.getElementById('zoomIndicator');
            if (existingIndicator) {
                existingIndicator.remove();
            }
            
            const existingResetBtn = document.getElementById('resetZoom');
            if (existingResetBtn) {
                existingResetBtn.remove();
            }
            
            // Update UI
            startCameraBtn.disabled = false;
            stopCameraBtn.disabled = true;
            updateStatus('Camera stopped', true);
        }
    }

    function startFrameProcessing() {
        // Clear any existing interval
        if (processingInterval) {
            clearInterval(processingInterval);
        }
        
        // Process frames at the configured interval
        processingInterval = setInterval(() => {
            if (!isProcessing && socket.connected) {
                captureAndSendFrame();
            }
        }, PROCESSING.processEveryMs);
    }

    function captureAndSendFrame() {
        if (!stream) return;
        
        try {
            // Draw current video frame to canvas
            captureContext.drawImage(cameraFeed, 0, 0, captureCanvas.width, captureCanvas.height);
            
            // Get image data as base64
            const imageData = captureCanvas.toDataURL('image/jpeg', 0.6);
            
            // Send to server for processing
            isProcessing = true;
            socket.emit('frame', { image: imageData });
        } catch (error) {
            console.error('Error capturing frame:', error);
            isProcessing = false;
        }
    }

    function updateMarkerList(markers) {
        if (!markers || markers.length === 0) {
            // Clear markers that haven't been seen for more than the timeout
            const currentTime = Date.now() / 1000;
            Object.keys(detectedMarkers).forEach(id => {
                if (currentTime - detectedMarkers[id].timestamp > PROCESSING.markerTimeoutSeconds) {
                    delete detectedMarkers[id];
                }
            });
        } else {
            // Update detected markers
            markers.forEach(marker => {
                detectedMarkers[marker.id] = {
                    id: marker.id,
                    timestamp: marker.timestamp
                };
            });
        }
        
        // Update UI list
        markerList.innerHTML = '';
        if (Object.keys(detectedMarkers).length === 0) {
            const li = document.createElement('li');
            li.textContent = 'No markers detected';
            markerList.appendChild(li);
        } else {
            Object.values(detectedMarkers).forEach(marker => {
                const li = document.createElement('li');
                const date = new Date(marker.timestamp * 1000);
                const timeStr = date.toLocaleTimeString();
                li.textContent = `ID: ${marker.id}${'\u00A0'.repeat(4)}(Last seen: ${timeStr})`;
                markerList.appendChild(li);
            });
        }
    }

    function updateStatus(message, isError = false) {
        statusMessage.textContent = message;
        statusMessage.style.borderLeftColor = isError ? '#f44336' : '#4caf50';
        console.log(message);
    }

    function initZoomControls() {
        // Add zoom controls to the UI
        const zoomControlsDiv = document.createElement('div');
        zoomControlsDiv.className = 'zoom-controls';
        
        // Add a zoom indicator
        const zoomIndicator = document.createElement('div');
        zoomIndicator.id = 'zoomIndicator';
        zoomIndicator.className = 'zoom-indicator';
        zoomIndicator.textContent = '1.0x';
        document.querySelector('.video-container').appendChild(zoomIndicator);
        
        // Add reset zoom button
        const resetZoomBtn = document.createElement('button');
        resetZoomBtn.id = 'resetZoom';
        resetZoomBtn.className = 'btn reset-zoom-btn';
        resetZoomBtn.textContent = 'Reset Zoom';
        resetZoomBtn.style.display = 'none';
        document.querySelector('.video-container').appendChild(resetZoomBtn);
        
        // Reset zoom button click event
        resetZoomBtn.addEventListener('click', () => {
            applyZoom(minZoom);
            updateZoomIndicator(minZoom);
            // Hide reset button after a delay
            clearTimeout(zoomIndicatorTimeout);
            zoomIndicatorTimeout = setTimeout(() => {
                resetZoomBtn.style.display = 'none';
            }, 1000);
        });
        
        // Setup touch events for pinch zoom
        const videoContainer = document.querySelector('.video-container');
        
        let startDistance = 0;
        let initialZoom = 1.0;
        let pinchInProgress = false;
        let zoomIndicatorTimeout;
        
        videoContainer.addEventListener('touchstart', (e) => {
            if (e.touches.length === 2) {
                e.preventDefault();
                // Get initial distance between the two touch points
                startDistance = getTouchDistance(e.touches);
                initialZoom = zoomLevel;
                pinchInProgress = true;
            }
        }, { passive: false });
        
        videoContainer.addEventListener('touchmove', (e) => {
            if (pinchInProgress && e.touches.length === 2) {
                e.preventDefault();
                
                // Calculate new distance and derive zoom factor
                const currentDistance = getTouchDistance(e.touches);
                const zoomFactor = currentDistance / startDistance;
                
                // Calculate new zoom level
                let newZoom = initialZoom * zoomFactor;
                
                // Clamp zoom level to min/max
                newZoom = Math.max(minZoom, Math.min(maxZoom, newZoom));
                
                // Apply zoom to camera
                applyZoom(newZoom);
                
                // Update indicator
                updateZoomIndicator(newZoom);
                
                // Show reset button if zoomed in
                if (newZoom > minZoom) {
                    resetZoomBtn.style.display = 'block';
                }
            }
        }, { passive: false });
        
        videoContainer.addEventListener('touchend', (e) => {
            if (pinchInProgress) {
                pinchInProgress = false;
                
                // Hide reset button if zoomed all the way out
                if (zoomLevel <= minZoom || Math.abs(zoomLevel - minZoom) < 0.1) {
                    resetZoomBtn.style.display = 'none';
                }
            }
        });
        
        // Function to calculate distance between two touch points
        function getTouchDistance(touches) {
            const dx = touches[0].pageX - touches[1].pageX;
            const dy = touches[0].pageY - touches[1].pageY;
            return Math.sqrt(dx * dx + dy * dy);
        }
        
        // Function to apply zoom to the camera
        function applyZoom(newZoom) {
            if (videoTrack && videoTrack.getCapabilities().zoom) {
                const constraints = { advanced: [{ zoom: newZoom }] };
                videoTrack.applyConstraints(constraints)
                    .then(() => {
                        zoomLevel = newZoom;
                        
                        // Hide reset button if zoomed all the way out
                        if (zoomLevel <= minZoom || Math.abs(zoomLevel - minZoom) < 0.1) {
                            resetZoomBtn.style.display = 'none';
                        }
                    })
                    .catch(error => {
                        console.error('Error applying zoom:', error);
                    });
            }
        }
        
        // Function to update zoom indicator
        function updateZoomIndicator(zoom) {
            const indicator = document.getElementById('zoomIndicator');
            indicator.textContent = `${zoom.toFixed(1)}x`;
        }
    }
}); 