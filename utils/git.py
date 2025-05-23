import configparser
import logging
import typing
from pathlib import Path

import httpx
from django.utils.functional import cached_property

logger = logging.getLogger(__name__)


class GitHelper:
    def __init__(self, project_base_dir: Path):
        self.base_dir = project_base_dir / ".git"
        self.head_path = self.base_dir / "HEAD"
        self.config_path = self.base_dir / "config"

    @staticmethod
    def ssh_to_https(url: str) -> str:
        """
        Converts git@github.com:mapswipe/mapswipe-backend.git -> https://github.com/mapswipe/mapswipe-backend
        """
        if url.startswith("git@"):
            user_host, repo_path = url.split(":", 1)
            host = user_host[4:]
            # Remove trailing .git if present
            if repo_path.endswith(".git"):
                repo_path = repo_path[:-4]
            return f"https://{host}/{repo_path}"
        # Also remove .git if URL is already https and ends with it
        if url.endswith(".git"):
            return url[:-4]
        return url

    @cached_property
    def branch(self) -> str | None:
        try:
            with Path.open(self.head_path, "r") as f:
                content = f.read().strip()
            if content.startswith("ref:"):
                return content.split("refs/heads/")[-1]
            return None
        except Exception:
            logger.warning("Failed to get git branch name", exc_info=True)
            return None

    @cached_property
    def repository_url(self) -> str | None:
        try:
            git_config_path = self.config_path
            config = configparser.ConfigParser(strict=False)
            config.read(git_config_path)

            # The section is usually like: remote "origin"
            # ConfigParser requires exact section name including quotes
            for section in config.sections():
                if section.startswith("remote ") and "origin" in section:
                    return self.ssh_to_https(config[section]["url"])
        except Exception:
            logger.warning("Failed to get git repository url", exc_info=True)

        return None

    @cached_property
    def commit_sha(self) -> str | None:
        try:
            with Path.open(self.head_path, "r") as f:
                ref = f.readline().strip()

            if ref.startswith("ref:"):
                # It's a symbolic ref
                ref_path = self.base_dir / ref[5:].strip()
                with Path.open(ref_path) as f:
                    commit_hash = f.readline().strip()
            else:
                # Detached HEAD, commit hash is in HEAD directly
                commit_hash = ref
            return commit_hash
        except Exception:
            logger.warning("Failed to get git commit hash", exc_info=True)
        return None

    @cached_property
    def commit_url(self) -> str | None:
        if repo_url := self.repository_url:
            return f"{repo_url}/commit/{self.commit_sha}"
        return None

    @cached_property
    def branch_url(self) -> str | None:
        if repo_url := self.repository_url:
            return f"{repo_url}/compare/{self.branch}"
        return None

    @cached_property
    def commit_github_metadata(self) -> typing.Any | None:
        try:
            if self.repository_url is None:
                return None
            repository_name = self.repository_url.split("https://github.com/")[1]
            resp = httpx.get(
                f"https://api.github.com/repos/{repository_name}/commits/{self.commit_sha}",
                timeout=2,
            )
            data = resp.json()
            # NOTE: The 'files' field in the GitHub commit response contains full diffs,
            # which can be very large and are not needed here
            data.pop("files", None)
            return data
        except Exception:
            logger.warning("Failed to fetch commit data from github", exc_info=True)
