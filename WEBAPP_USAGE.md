# ArUco Marker Scanner Web App - Usage Guide

This guide explains how to set up and use the web app version of the ArUco Marker Scanner on mobile devices.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Deploy the app online (see Deployment section below)

3. Access the app from any device using your deployed URL

## Using The App

1. When the app loads, tap "Start Camera"
2. Allow camera access when prompted by your browser
3. For devices with multiple cameras, select the rear camera
4. Point your camera at ArUco markers
5. Detected markers will be highlighted and their IDs displayed
6. The marker list will show all recently detected markers

## Troubleshooting

### Camera Access Issues
- Make sure you're using HTTPS (required for camera access)
- Check that your browser has permission to access the camera
- Try a different browser (Chrome or Safari recommended)

### Performance Issues
- Reduce video quality in `config.py` if the app is slow
- Make sure you have a stable network connection
- Close other tabs and applications on your device

### Marker Detection Issues
- Ensure adequate lighting for marker detection
- Hold the device steady to avoid motion blur
- Make sure the markers are clean and flat (not wrinkled)
- Try different distances between the camera and markers

## Customization

Edit `config.py` to customize:
- Server settings (port, host, etc.)
- Processing settings (image quality, processing frequency)
- Marker settings (timeout, default dictionary)

## Deployment Options

For deployment, you have several options:

### 1. Heroku Deployment
```bash
# Install Heroku CLI and login
heroku login

# Create a new Heroku app
heroku create your-marker-scanner

# Push to Heroku
git push heroku main

# Scale the web process
heroku ps:scale web=1
```

### 2. PythonAnywhere or Similar Services
- Upload your files
- Set up a WSGI configuration
- Enable WebSocket support (check service compatibility)

### 3. Cloud VPS (AWS, GCP, Azure, DigitalOcean)
- Set up a virtual server
- Install dependencies
- Run with a production WSGI server:
  ```
  gunicorn --worker-class eventlet -w 1 app:app
  ```
- Set up HTTPS with Let's Encrypt

### 4. Docker Deployment
Create a Dockerfile:
```
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:5000", "app:app"]
```

Then build and run:
```bash
docker build -t marker-scanner .
docker run -p 5000:5000 marker-scanner
```

## HTTPS Setup (Required)

Most browsers require HTTPS for camera access. Options:

1. Use a service with built-in HTTPS (Heroku, Render, etc.)
2. Set up your own with Let's Encrypt:
   ```bash
   sudo apt-get install certbot
   sudo certbot certonly --standalone -d yourdomain.com
   ```

3. Configure your web server (Nginx example):
   ```
   server {
       listen 443 ssl;
       server_name yourdomain.com;
       
       ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
       
       location / {
           proxy_pass http://localhost:5000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
   }
   ```

## Security Considerations

Before deployment:
1. Change the secret key in `config.py`
2. Disable debug mode
3. Set specific CORS origins instead of '*'

## Help and Support

If you encounter issues:
1. Check that markers.txt file exists and contains valid markers
2. Verify that all required packages are installed
3. Test on different browsers and devices 