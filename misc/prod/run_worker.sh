#!/bin/bash -e

./manage.py wait_for_resources --redis

celery -A main worker \
    -l INFO \
    -Q default \
    --concurrency 4 \
    --max-tasks-per-child 10
