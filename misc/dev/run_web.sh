#!/bin/bash -e

wait-for-it "$POSTGRES_HOST:$POSTGRES_PORT"

./manage.py runserver 0.0.0.0:8000
