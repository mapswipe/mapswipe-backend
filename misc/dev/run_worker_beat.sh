#!/bin/bash -e

./manage.py wait_for_resources --db --celery-broker

celery -A main beat -l info
