#!/bin/bash

# Activate virtual environment
source /opt/venv/bin/activate

# Wait for postgres
echo "Waiting for postgres..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Start server
echo "Starting server..."
exec "$@"
