# Marker Scanner Web App

A web-based version of the ArUco Marker Scanner, designed to work on mobile devices through web browsers with online deployment.

## Features

- Works on mobile devices (Android and iOS) through web browsers
- Access camera on mobile devices
- Real-time ArUco marker detection
- Display marker IDs and detection timestamps
- Camera selection for devices with multiple cameras

## Requirements

- Python 3.6+
- Flask and Flask-SocketIO
- OpenCV with ArUco module
- Modern web browser with camera access support
- HTTPS support (required for camera access)

## Installation

1. Clone this repository
2. Install the required packages:

```bash
pip install -r requirements.txt
```

## Deployment Options

### Option 1: Heroku Deployment

1. Create a `requirements.txt` file with all dependencies (already done)
2. Create a `Procfile` (already created)
3. Deploy to Heroku:

```bash
# Install Heroku CLI
npm install -g heroku

# Login to Heroku
heroku login

# Create a new app
heroku create your-marker-scanner-app

# Deploy the app
git push heroku main

# Scale the app
heroku ps:scale web=1
```

### Option 2: Docker Deployment

1. Build the Docker image:

```bash
docker build -t marker-scanner .
```

2. Run the container:

```bash
docker run -p 5000:5000 marker-scanner
```

3. Deploy to a cloud service that supports Docker (AWS ECS, Google Cloud Run, etc.)

### Option 3: Traditional VPS

1. Set up a VPS (AWS EC2, DigitalOcean, etc.)
2. Install the requirements
3. Set up a production WSGI server:

```bash
gunicorn --worker-class eventlet -w 1 app:app
```

4. Set up a reverse proxy with Nginx/Apache
5. Configure SSL with Let's Encrypt

## Environment Variables

For secure deployment, the following environment variables can be set:

- `SECRET_KEY`: Flask secret key
- `PORT`: Server port (default: 5000)
- `DEBUG`: Enable debug mode (default: False)
- `MARKERS_FILE`: Path to markers file (default: markers.txt)
- `FRAME_QUALITY`: JPEG quality for transmission (default: 0.7)
- `MAX_WIDTH`: Maximum processing width (default: 640)
- `MAX_HEIGHT`: Maximum processing height (default: 480)
- `PROCESS_RATE`: Frame processing rate in ms (default: 100)
- `CORS_ORIGINS`: CORS allowed origins (default: *)
- `MARKER_TIMEOUT`: How long to show markers after detection (default: 3)

## How It Works

- The mobile browser accesses the device's camera and sends frames to the server
- Flask backend processes frames using OpenCV to detect ArUco markers
- Processed frames are sent back to the browser via WebSockets
- The browser displays the processed frames and marker information

## Mobile Browser Compatibility

- **Android**: Chrome, Firefox, Samsung Internet
- **iOS**: Safari, Chrome

## Security Considerations

1. Always use HTTPS in production (required for camera access)
2. Set a strong SECRET_KEY
3. Set specific CORS origins in production
4. Disable debug mode in production

## License

This project is open source and available under the MIT License. 