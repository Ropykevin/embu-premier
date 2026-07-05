#!/bin/sh
set -e

PORT="${PORT:-8005}"
WORKERS="${GUNICORN_WORKERS:-2}"
TIMEOUT="${GUNICORN_TIMEOUT:-120}"

DB_HOST="${POSTGRES_HOST:-db}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_NAME="${POSTGRES_DB:-embu_premier_clinic}"

echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; do
  sleep 2
done
echo "PostgreSQL is ready."

echo "Running database migrations..."
flask db upgrade

echo "Ensuring admin user exists..."
flask init-db

echo "Starting Gunicorn on 0.0.0.0:${PORT} with ${WORKERS} workers..."
exec gunicorn wsgi:app \
  --bind "0.0.0.0:${PORT}" \
  --workers "${WORKERS}" \
  --timeout "${TIMEOUT}" \
  --access-logfile - \
  --error-logfile -
