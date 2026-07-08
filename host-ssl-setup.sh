#!/bin/bash
#
# SSL + reverse proxy via the VPS host nginx (when port 80 is already in use).
#
# Usage:
#   sudo ./host-ssl-setup.sh embupremierphysicians.co.ke admin@example.com
#
set -e

DOMAIN="${1:-}"
EMAIL="${2:-}"
WEB_PORT="${WEB_PORT:-8005}"
SITE_NAME="embu-premier"
NGINX_AVAILABLE="/etc/nginx/sites-available/${SITE_NAME}"
NGINX_ENABLED="/etc/nginx/sites-enabled/${SITE_NAME}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root: sudo ./host-ssl-setup.sh <domain> <email>"
  exit 1
fi

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
  echo "Usage: sudo ./host-ssl-setup.sh <domain> <email>"
  echo "Example: sudo ./host-ssl-setup.sh embupremierphysicians.co.ke admin@clinic.com"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE="${SCRIPT_DIR}/nginx/host/embu-premier.conf.template"

if [ ! -f "$TEMPLATE" ]; then
  echo "Template not found: $TEMPLATE"
  exit 1
fi

if ! command -v nginx >/dev/null 2>&1; then
  echo "Host nginx is not installed."
  exit 1
fi

echo "Checking DNS for ${DOMAIN}..."
RESOLVED_IP="$(getent ahostsv4 "$DOMAIN" 2>/dev/null | awk '{print $1; exit}')"
PUBLIC_IP="$(curl -4 -s ifconfig.me 2>/dev/null || true)"
if [ -n "$RESOLVED_IP" ] && [ -n "$PUBLIC_IP" ] && [ "$RESOLVED_IP" != "$PUBLIC_IP" ]; then
  echo "WARN: ${DOMAIN} resolves to ${RESOLVED_IP}, but this server is ${PUBLIC_IP}."
  echo "Fix DNS before continuing, or certbot may fail."
fi

echo "Writing ${NGINX_AVAILABLE}..."
sed -e "s/\${DOMAIN}/${DOMAIN}/g" -e "s/\${WEB_PORT}/${WEB_PORT}/g" \
  "$TEMPLATE" > "$NGINX_AVAILABLE"

if [ ! -e "$NGINX_ENABLED" ]; then
  ln -s "$NGINX_AVAILABLE" "$NGINX_ENABLED"
fi

nginx -t
systemctl reload nginx

echo "Requesting Let's Encrypt certificate..."
if command -v certbot >/dev/null 2>&1; then
  certbot --nginx -d "$DOMAIN" --email "$EMAIL" --agree-tos --no-eff-email --redirect
else
  echo "certbot not found. Install it, then run:"
  echo "  sudo apt update && sudo apt install -y certbot python3-certbot-nginx"
  echo "  sudo certbot --nginx -d ${DOMAIN} --email ${EMAIL} --agree-tos --no-eff-email --redirect"
  exit 1
fi

nginx -t
systemctl reload nginx

echo ""
echo "Host nginx SSL setup complete."
echo "Site: https://${DOMAIN}"
echo ""
echo "Update ~/opt/embu-premier/.env on this server:"
echo "  DOMAIN=${DOMAIN}"
echo "  HTTPS_ENABLED=true"
echo "  SESSION_COOKIE_SECURE=true"
echo ""
echo "Then restart the web container:"
echo "  cd ~/opt/embu-premier && docker compose -f docker-compose.prod.yml up -d web"
