import signal
import time
import typing
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandParser
from django.db import connections
from django.db.utils import OperationalError
from redis.exceptions import ConnectionError as RedisConnectionError


class TimeoutException(Exception): ...


def timeout_handler(*_):
    raise Exception("The command timed out.")


class Command(BaseCommand):
    help = "Wait for resources our application depends on"

    def wait_for_db(self):
        self.stdout.write("Waiting for DB...")
        db_conn = None
        start_time = time.time()
        while True:
            try:
                db_conn = connections["default"]
                db_conn.ensure_connection()
                break
            except OperationalError:
                ...
            # Try again
            self.stdout.write(self.style.WARNING("DB not available, waiting..."))
            time.sleep(1)

        self.stdout.write(self.style.SUCCESS(f"DB is available after {time.time() - start_time} seconds"))

    def wait_for_redis(self):
        self.stdout.write("Waiting for Redis...")
        redis_conn = None
        start_time = time.time()
        while True:
            try:
                cache.set("wait-for-it-ping", "pong", timeout=1)  # Set a key to check Redis availability
                redis_conn = cache.get("wait-for-it-ping")  # Try to get the value back from Redis
                if redis_conn != "pong":
                    raise TypeError
                break
            except (RedisConnectionError, TypeError):
                ...
            # Try again
            self.stdout.write(self.style.WARNING("Redis not available, waiting..."))
            time.sleep(1)

        self.stdout.write(self.style.SUCCESS(f"Redis is available after {time.time() - start_time} seconds"))

    def wait_for_minio(self):
        self.stdout.write("Waiting for Minio...")
        AWS_S3_CONFIG_OPTIONS = getattr(settings, "AWS_S3_CONFIG_OPTIONS", None) or {}
        endpoint_url = AWS_S3_CONFIG_OPTIONS.get("endpoint_url")
        if endpoint_url is None:
            self.stdout.write(self.style.WARNING("No endpoint_url is provided. Skipping wait"))
            return

        start_time = time.time()
        while True:
            try:
                response = requests.get(urljoin(endpoint_url, "/minio/health/live"), timeout=5)
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                ...
            # Try again
            self.stdout.write(self.style.WARNING("Minio not available, waiting..."))
            time.sleep(5)

        self.stdout.write(self.style.SUCCESS(f"Minio is available after {time.time() - start_time} seconds"))

    @typing.override
    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            "--timeout",
            "--timeout",
            type=int,
            default=600,
            help="The maximum time (in seconds) the command is allowed to run before timing out. Default is 10 min.",
        )
        parser.add_argument("--db", action="store_true", help="Wait for DB to be available")
        parser.add_argument("--celery-queue", action="store_true", help="Wait for Celery queue to be available")
        parser.add_argument("--redis", action="store_true", help="Wait for Redis to be available")
        parser.add_argument("--minio", action="store_true", help="Wait for MinIO (S3) storage to be available")
        parser.add_argument("--all", action="store_true", help="Wait for all to be available")

    @typing.override
    def handle(self, **kwargs: typing.Any):
        timeout = kwargs["timeout"]
        _all = kwargs["all"]

        # Set the timeout handler (1 minute = 60 seconds)
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)

        try:
            if _all or kwargs["db"]:
                self.wait_for_db()
            if _all or kwargs["minio"]:
                self.wait_for_minio()
            if _all or kwargs["redis"]:
                self.wait_for_redis()
            if _all or kwargs["celery_queue"]:
                self.wait_for_redis()
        except TimeoutException:
            ...
        finally:
            # Disable the alarm (cleanup)
            signal.alarm(0)
