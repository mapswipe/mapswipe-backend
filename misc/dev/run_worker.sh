#!/bin/bash -e

./manage.py wait_for_resources --db --celery-broker

./manage.py run_celery_dev
