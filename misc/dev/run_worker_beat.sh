#!/bin/bash -e

./manage.py wait_for_resources --db --celery-queue

celery -A main beat -l info
