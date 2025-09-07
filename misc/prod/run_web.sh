#!/bin/bash -e

./manage.py wait_for_resources --db

gunicorn "main.wsgi:application" \
    --bind=0.0.0.0:80 \
    --timeout=40
