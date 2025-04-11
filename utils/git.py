import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class InvalidGitRepository(Exception):
    pass


def fetch_git_sha(path: Path, head: str | None = None, raise_on_error: bool = True) -> str | None:
    """
    Source: https://github.com/getsentry/raven-python/blob/03559bb05fd963e2be96372ae89fb0bce751d26d/raven/versioning.py
    >>> fetch_git_sha(os.path.dirname(__file__))
    """
    if not head:
        head_path = path / ".git/HEAD"
        if not head_path.exists():
            error_message = f"Cannot identify HEAD for git repository at {path}"
            if raise_on_error:
                raise InvalidGitRepository(error_message)
            logger.warning(error_message)
            return None

        with head_path.open("r") as fp:
            head = str(fp.read()).strip()

        if head.startswith("ref: "):
            head = head[5:]
            revision_file = path.joinpath(".git", *head.split("/"))
        else:
            return head
    else:
        revision_file = path / ".git/refs/heads" / head

    if not revision_file.exists():
        if not (path / ".git").exists():
            error_message = f"{path} does not seem to be the root of a git repository"
            if raise_on_error:
                raise InvalidGitRepository(error_message)
            logger.warning(error_message)
            return None

        # Check for our .git/packed-refs' file since a `git gc` may have run
        # https://git-scm.com/book/en/v2/Git-Internals-Maintenance-and-Data-Recovery
        packed_file = path / ".git/packed-refs"
        if packed_file.exists():
            with packed_file.open() as fh:
                for line in fh:
                    line = line.rstrip()
                    if line and line[:1] not in ("#", "^"):
                        try:
                            revision, ref = line.split(" ", 1)
                        except ValueError:
                            continue
                        if ref == head:
                            return str(revision)

        error_message = f'Unable to find ref to head "{head}" in repository'
        if raise_on_error:
            raise InvalidGitRepository(error_message)
        logger.warning(error_message)
        return None

    with revision_file.open() as fh:
        return str(fh.read()).strip()
