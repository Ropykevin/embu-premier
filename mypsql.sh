#!/bin/bash
#
# PostgreSQL helper for Embu Premier Clinic on DatabaseMart VPS
#
# Usage:
#   ./mypsql.sh setup          Create .env and backups folder
#   ./mypsql.sh up             Start all containers
#   ./mypsql.sh down           Stop all containers
#   ./mypsql.sh restart        Restart all containers
#   ./mypsql.sh logs           Tail web + db logs
#   ./mypsql.sh status         Show container and database status
#   ./mypsql.sh shell          Open psql shell in db container
#   ./mypsql.sh backup         Dump database to ./backups/
#   ./mypsql.sh restore FILE   Restore database from backup file
#   ./mypsql.sh init           Run Flask init-db in web container
#   ./mypsql.sh migrate        Run Flask db upgrade in web container
#   ./mypsql.sh stamp          Mark existing DB as migrated
#   ./mypsql.sh prod-up        Start production stack (nginx + SSL ready)
#   ./mypsql.sh prod-down      Stop production stack
#   ./mypsql.sh ssl DOMAIN EMAIL  Obtain Let's Encrypt certificate
#   ./mypsql.sh test           Run pytest inside web container
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

COMPOSE="docker compose"
if ! docker compose version >/dev/null 2>&1; then
  COMPOSE="docker-compose"
fi

load_env() {
  if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
  fi
}

POSTGRES_DB="${POSTGRES_DB:-embu_premier_clinic}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"

ensure_env() {
  if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "IMPORTANT: Edit .env and set strong values for:"
    echo "  SECRET_KEY"
    echo "  POSTGRES_PASSWORD"
    echo "  ADMIN_PASSWORD"
    echo ""
  fi
}

ensure_backup_dir() {
  mkdir -p "$BACKUP_DIR"
}

cmd_setup() {
  ensure_env
  ensure_backup_dir
  echo "Setup complete."
  echo "Next steps:"
  echo "  1. Edit .env"
  echo "  2. ./mypsql.sh up"
}

cmd_up() {
  load_env
  ensure_backup_dir
  $COMPOSE up -d --build
  echo ""
  echo "Dev stack running on http://127.0.0.1:${WEB_PORT:-8000} (localhost only)"
  echo "For VPS production use: ./mypsql.sh prod-up"
}

cmd_down() {
  $COMPOSE down
}

cmd_restart() {
  $COMPOSE restart
}

cmd_logs() {
  $COMPOSE logs -f web db
}

cmd_status() {
  echo "=== Docker containers ==="
  $COMPOSE ps
  echo ""
  echo "=== PostgreSQL readiness ==="
  $COMPOSE exec -T db pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" || true
  echo ""
  echo "=== Database size ==="
  $COMPOSE exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
    "SELECT pg_size_pretty(pg_database_size('${POSTGRES_DB}')) AS db_size;" || true
}

cmd_shell() {
  load_env
  $COMPOSE exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
}

cmd_backup() {
  load_env
  ensure_backup_dir
  TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
  BACKUP_FILE="${BACKUP_DIR}/${POSTGRES_DB}_${TIMESTAMP}.sql"

  echo "Creating backup: ${BACKUP_FILE}"
  $COMPOSE exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" > "$BACKUP_FILE"
  echo "Backup saved to ${BACKUP_FILE}"
}

cmd_restore() {
  load_env
  RESTORE_FILE="$1"

  if [ -z "$RESTORE_FILE" ]; then
    echo "Usage: ./mypsql.sh restore backups/your_backup.sql"
    exit 1
  fi

  if [ ! -f "$RESTORE_FILE" ]; then
    echo "Backup file not found: $RESTORE_FILE"
    exit 1
  fi

  echo "Restoring ${RESTORE_FILE} into ${POSTGRES_DB}..."
  $COMPOSE exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$RESTORE_FILE"
  echo "Restore complete."
}

cmd_init() {
  $COMPOSE exec web flask init-db
}

cmd_migrate() {
  $COMPOSE exec web flask db upgrade
}

cmd_stamp() {
  echo "Marking existing database as fully migrated (all revisions)..."
  $COMPOSE exec web flask db stamp head
}

cmd_prod_up() {
  load_env
  ensure_backup_dir
  mkdir -p certbot/www certbot/conf nginx/conf.d
  cp nginx/conf.d/default.http.conf nginx/conf.d/default.conf
  $COMPOSE -f docker-compose.prod.yml up -d --build
  echo ""
  echo "Production stack running on ports 80 and 443."
  echo "Run ./ssl-setup.sh yourdomain.com you@email.com for HTTPS."
}

cmd_prod_down() {
  $COMPOSE -f docker-compose.prod.yml down
}

cmd_ssl() {
  if [ -z "${2:-}" ] || [ -z "${3:-}" ]; then
    echo "Usage: ./mypsql.sh ssl yourdomain.com admin@yourdomain.com"
    exit 1
  fi
  chmod +x ssl-setup.sh
  ./ssl-setup.sh "$2" "$3"
}

cmd_test() {
  $COMPOSE exec web pytest
}

case "${1:-}" in
  setup)
    cmd_setup
    ;;
  up)
    cmd_up
    ;;
  down)
    cmd_down
    ;;
  restart)
    cmd_restart
    ;;
  logs)
    cmd_logs
    ;;
  status)
    load_env
    cmd_status
    ;;
  shell)
    cmd_shell
    ;;
  backup)
    cmd_backup
    ;;
  restore)
    cmd_restore "$2"
    ;;
  init)
    cmd_init
    ;;
  migrate)
    cmd_migrate
    ;;
  stamp)
    cmd_stamp
    ;;
  prod-up)
    cmd_prod_up
    ;;
  prod-down)
    cmd_prod_down
    ;;
  ssl)
    cmd_ssl "$@"
    ;;
  test)
    cmd_test
    ;;
  *)
    echo "Embu Premier Clinic - DatabaseMart VPS helper"
    echo ""
    echo "Usage: ./mypsql.sh {setup|up|down|restart|logs|status|shell|backup|restore|init|migrate|stamp|prod-up|prod-down|ssl|test}"
    exit 1
    ;;
esac
