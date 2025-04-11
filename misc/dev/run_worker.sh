#!/bin/bash -e

REDIS_HOST_PORT=$(echo $CELERY_REDIS_URL | sed 's|redis://\([^/]*\)/.*|\1|')

./manage.py wait_for_resources --db --celery-queue

./manage.py run_celery_dev
