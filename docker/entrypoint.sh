#!/bin/sh
set -eu

if [ "$1" = "web" ]; then
    python manage.py migrate --noinput
    exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
elif [ "$1" = "worker" ]; then
    exec celery -A config worker --loglevel=info
elif [ "$1" = "beat" ]; then
    exec celery -A config beat --loglevel=info
else
    exec "$@"
fi
