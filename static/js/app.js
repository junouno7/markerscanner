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
    
    // Processing settings - these should match server settings
    const PROCESSING = {
        processEveryMs: 100,  // Process frames every 100ms by default
        markerTimeoutSeconds: 3  // How long to keep markers visible
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
                    height: { ideal: 480 }
                }
            };

            // If a specific camera is selected, use it
            if (cameraSelect.value) {
                constraints.video = {
                    deviceId: { exact: cameraSelect.value },
                    width: { ideal: 640 },
                    height: { ideal: 480 }
                };
            }

            // Get user media
            stream = await navigator.mediaDevices.getUserMedia(constraints);
            cameraFeed.srcObject = stream;
            
            // Set canvas size to match video
            captureCanvas.width = 640;
            captureCanvas.height = 480;

            // Update UI
            startCameraBtn.disabled = true;
            stopCameraBtn.disabled = false;
            updateStatus('Camera started');

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
            
            // Update UI
            startCameraBtn.disabled = false;
            stopCameraBtn.disabled = true;
            updateStatus('Camera stopped');
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
            const imageData = captureCanvas.toDataURL('image/jpeg', 0.7);
            
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
                li.textContent = `Marker ID: ${marker.id} (Last seen: ${timeStr})`;
                markerList.appendChild(li);
            });
        }
    }

    function updateStatus(message, isError = false) {
        statusMessage.textContent = message;
        statusMessage.style.borderLeftColor = isError ? '#f44336' : '#4caf50';
        console.log(message);
    }
}); 