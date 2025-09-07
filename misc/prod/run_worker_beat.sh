#!/bin/bash -e

./manage.py wait_for_resources --redis

celery -A main beat \
    -l INFO
