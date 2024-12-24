#!/bin/bash

# Exit on error
set -e

# Check if domain is provided
if [ -z "$1" ]; then
    echo "Usage: ./deploy.sh <your-domain>"
    exit 1
fi

DOMAIN=$1

# Create necessary directories
mkdir -p certbot/conf certbot/www

# Replace domain in nginx config
sed -i.bak "s/YOUR_DOMAIN/$DOMAIN/g" nginx.conf

# Generate strong JWT secret
JWT_SECRET=$(openssl rand -base64 32)

# Create .env file
cat > .env << EOL
JWT_SECRET=$JWT_SECRET
FLASK_ENV=production
MAX_CONTENT_LENGTH=100000000
EOL

# Initialize Docker Swarm (if not already initialized)
if ! docker info | grep -q "Swarm: active"; then
    docker swarm init
fi

# Deploy the stack
docker stack deploy -c docker-compose.prod.yml ntsc

# Wait for services to start
echo "Waiting for services to start..."
sleep 30

# Initialize SSL certificate
docker run --rm \
    -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
    -v "$(pwd)/certbot/www:/var/www/certbot" \
    certbot/certbot certonly \
    --webroot --webroot-path /var/www/certbot \
    --email admin@$DOMAIN --agree-tos --no-eff-email \
    -d $DOMAIN

# Reload nginx to apply SSL configuration
docker service update --force ntsc_nginx

echo "Deployment completed!"
echo "Your API is now available at https://$DOMAIN"
echo ""
echo "Test the API with:"
echo "curl -X POST -u demo:password https://$DOMAIN/auth"
echo ""
echo "Then use the token to upload a video:"
echo 'curl -X POST -H "Authorization: Bearer YOUR_TOKEN" -F "video=@video.mp4" https://$DOMAIN/upload -o processed_video.mp4'
