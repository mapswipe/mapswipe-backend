FROM python:3.13-slim-bookworm AS base
COPY --from=ghcr.io/astral-sh/uv:0.6.2 /uv /uvx /bin/

LABEL maintainer="Mapswipe Dev"
LABEL org.opencontainers.image.source="https://github.com/mapswipe/mapswipe-backend/"

ENV PYTHONUNBUFFERED=1

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"

WORKDIR /code

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    apt-get update -y \
    # FIXME(thenav56): Check and clean up not required packages from here
    && apt-get install -y --no-install-recommends \
        # Build required packages
        gdal-bin build-essential gcc libc-dev libgdal-dev libproj-dev \
        # Helper packages
        procps \
    && uv lock --locked --offline \
        && uv sync --frozen --no-install-project --all-groups \
    # Clean-up
    && apt-get remove -y build-essential gcc libc-dev libgdal-dev libproj-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*


COPY . /code/
