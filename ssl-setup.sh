#!/bin/bash
#
# Obtain or renew Let's Encrypt SSL certificate on DatabaseMart VPS.
#
# Usage:
#   ./ssl-setup.sh yourdomain.com admin@yourdomain.com
#
set -e

DOMAIN="${1:-}"
EMAIL="${2:-}"

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
  echo "Usage: ./ssl-setup.sh <domain> <email>"
  echo "Example: ./ssl-setup.sh clinic.example.com admin@example.com"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

COMPOSE="docker compose"
if ! docker compose version >/dev/null 2>&1; then
  COMPOSE="docker-compose"
fi

mkdir -p certbot/www certbot/conf nginx/conf.d

echo "Starting stack with HTTP-only nginx for certificate challenge..."
cp nginx/conf.d/default.http.conf nginx/conf.d/default.conf
$COMPOSE -f docker-compose.prod.yml --profile ssl up -d db web nginx

echo "Requesting certificate for ${DOMAIN}..."
docker run --rm \
  -v "$(pwd)/certbot/www:/var/www/certbot" \
  -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
  certbot/certbot certonly \
  --webroot \
  --webroot-path /var/www/certbot \
  --email "$EMAIL" \
  --agree-tos \
  --no-eff-email \
  -d "$DOMAIN"

echo "Generating HTTPS nginx config..."
sed "s/\${DOMAIN}/${DOMAIN}/g" nginx/conf.d/default.conf.template > nginx/conf.d/default.conf

echo "Restarting nginx with SSL..."
$COMPOSE -f docker-compose.prod.yml --profile ssl up -d nginx certbot

echo ""
echo "SSL setup complete."
echo "Site: https://${DOMAIN}"
echo ""
echo "Add to your .env:"
echo "  DOMAIN=${DOMAIN}"
echo "  HTTPS_ENABLED=true"
echo "  SESSION_COOKIE_SECURE=true"
echo ""
echo "Then restart the web container:"
echo "  docker compose -f docker-compose.prod.yml up -d web"
