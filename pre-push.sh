#!/usr/bin/env bash

BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

set -x

cd "$BASE_DIR"

pre-commit run --all-files

export SECRET_KEY="random-key-so-it-work-even-without-env-file"

docker compose run --rm web ./manage.py makemigrations --dry-run --verbosity 3
docker compose run --rm web ./manage.py graphql_schema --out schema.graphql
