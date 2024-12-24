# Video Effects Server

A web service that applies VHS/NTSC effects to videos using the ntsc-rs library.

## Local Development

1. Build and run the Docker container:
```bash
docker-compose up --build
```

2. The server will be available at `http://localhost:5001`

## Production Deployment (DigitalOcean)

1. Create a DigitalOcean Droplet (recommended: Basic Droplet with at least 2GB RAM)

2. Install Docker and Docker Compose on the Droplet:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get install docker-compose-plugin
```

3. Clone this repository on the Droplet:
```bash
git clone <your-repo-url>
cd video_effects_server
```

4. Set up your domain:
- Point your domain's A record to your Droplet's IP address
- Replace `YOUR_DOMAIN` in `nginx.conf` with your actual domain

5. Initialize SSL certificates:
```bash
mkdir -p certbot/conf certbot/www
docker-compose -f docker-compose.prod.yml up --build -d nginx
docker-compose -f docker-compose.prod.yml run --rm certbot certonly --webroot --webroot-path /var/www/certbot -d YOUR_DOMAIN
```

6. Start the production services:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## API Endpoints

- `POST /upload`: Upload a video file for processing
  - Request: multipart/form-data with 'video' field
  - Response: Processed video file

## Configuration

Environment variables (can be set in docker-compose.yml):
- `FLASK_ENV`: Set to 'production' for production deployment
- `MAX_CONTENT_LENGTH`: Maximum upload file size (default: 100MB)

## Notes

- Processed videos are temporarily stored in the container and deleted after being served
- Maximum video file size is 100MB by default
- The service uses Gunicorn as the WSGI server in production
