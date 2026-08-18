#!/bin/sh
set -eu

python manage.py collectstatic --noinput
python manage.py migrate --noinput

exec gunicorn \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers 1 \
  --threads 4 \
  --access-logfile - \
  --error-logfile - \
  config.wsgi:application
