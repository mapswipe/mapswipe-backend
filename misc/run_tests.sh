#!/bin/bash -x

CODE_DIR=${CODE_DIR:-/code}

wait-for-it "$POSTGRES_HOST:$POSTGRES_PORT"

if [ "$CI" == "true" ]; then
    pip3 install pytest-cov

    set -e

    # To show migration logs
    ./manage.py test --keepdb -v 2 main.tests.fake_test

    # Run all tests now
    py.test \
        --cov-config=.coveragerc \
        --cov \
        --cov-branch \
        --cov-report=xml \
        --junitxml=junit.xml \
        -o junit_family=legacy \
        --reuse-db \
        --durations=10
    coverage report -i

    set +e
else
    py.test
fi
