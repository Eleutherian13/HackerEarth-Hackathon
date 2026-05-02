#!/bin/bash
set -e

echo "Starting Celery worker..."
exec celery -A app.worker worker --loglevel=info
