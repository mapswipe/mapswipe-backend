import shlex
import subprocess
import typing
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils import autoreload

WORKER_STATE_DIR = Path("/var/run/celery")

CMD = "celery -A main worker -E --concurrency=2 -l info"


def restart_celery(*args: typing.Any, **kwargs: typing.Any):
    kill_worker_cmd = "pkill -9 celery"
    subprocess.call(shlex.split(kill_worker_cmd))  # noqa: S603
    subprocess.call(shlex.split(CMD))  # noqa: S603


class Command(BaseCommand):
    @typing.override
    def handle(self, *args: typing.Any, **options: typing.Any):
        self.stdout.write("Starting celery worker with autoreload...")
        if not Path.exists(WORKER_STATE_DIR):
            Path.mkdir(WORKER_STATE_DIR, parents=True)
        autoreload.run_with_reloader(restart_celery, args=None, kwargs=None)
