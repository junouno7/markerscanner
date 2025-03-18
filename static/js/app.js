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
    
    // Zoom variables
    let currentScale = 1;
    let lastScale = 1;
    let startDistance = 0;
    let isPinching = false;
    let startX = 0;
    let startY = 0;
    let lastX = 0;
    let lastY = 0;
    
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

        // Initialize zoom functionality
        initZoom();

        // Populate camera list
        populateCameraList();
    }

    // Initialize pinch-to-zoom functionality
    function initZoom() {
        const imageContainer = document.querySelector('.video-container');
        
        // Add reset zoom button
        const resetButton = document.createElement('button');
        resetButton.textContent = 'Reset Zoom';
        resetButton.className = 'btn reset-zoom';
        resetButton.style.position = 'absolute';
        resetButton.style.bottom = '10px';
        resetButton.style.right = '10px';
        resetButton.style.display = 'none';
        resetButton.style.zIndex = '100';
        resetButton.style.opacity = '0.7';
        resetButton.addEventListener('click', resetZoom);
        imageContainer.appendChild(resetButton);
        
        // Function to reset zoom
        function resetZoom() {
            currentScale = 1;
            lastScale = 1;
            lastX = 0;
            lastY = 0;
            updateTransform();
            resetButton.style.display = 'none';
        }
        
        // Function to update the transform
        function updateTransform() {
            processedImage.style.transformOrigin = 'center';
            processedImage.style.transform = `scale(${currentScale}) translate(${lastX}px, ${lastY}px)`;
        }
        
        // Touch start event
        processedImage.addEventListener('touchstart', (e) => {
            if (e.touches.length === 2) {
                // Pinch gesture starting
                isPinching = true;
                startDistance = getDistance(e.touches[0], e.touches[1]);
            } else if (e.touches.length === 1 && currentScale > 1) {
                // Start panning
                startX = e.touches[0].clientX - lastX;
                startY = e.touches[0].clientY - lastY;
            }
            e.preventDefault();
        });
        
        // Touch move event
        processedImage.addEventListener('touchmove', (e) => {
            if (isPinching && e.touches.length === 2) {
                // Calculate new scale
                const distance = getDistance(e.touches[0], e.touches[1]);
                const scale = distance / startDistance;
                
                currentScale = Math.max(1, Math.min(5, lastScale * scale)); // Limit zoom between 1x and 5x
                
                if (currentScale > 1) {
                    resetButton.style.display = 'block';
                }
                
                updateTransform();
            } else if (e.touches.length === 1 && currentScale > 1) {
                // Handle panning when zoomed in
                lastX = e.touches[0].clientX - startX;
                lastY = e.touches[0].clientY - startY;
                updateTransform();
            }
            e.preventDefault();
        });
        
        // Touch end event
        processedImage.addEventListener('touchend', (e) => {
            if (isPinching) {
                isPinching = false;
                lastScale = currentScale;
            }
            e.preventDefault();
        });
        
        // Calculate distance between two touch points
        function getDistance(touch1, touch2) {
            const dx = touch1.clientX - touch2.clientX;
            const dy = touch1.clientY - touch2.clientY;
            return Math.sqrt(dx * dx + dy * dy);
        }
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
}); 