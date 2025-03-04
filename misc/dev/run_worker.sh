#!/bin/bash -e

REDIS_HOST_PORT=$(echo $CELERY_REDIS_URL | sed 's|redis://\([^/]*\)/.*|\1|')

wait-for-it "$POSTGRES_HOST:$POSTGRES_PORT"
wait-for-it "$REDIS_HOST_PORT"

./manage.py run_celery_dev
