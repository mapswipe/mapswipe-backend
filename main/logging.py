import logging
import typing

import requests


def log_render_extra_context(record: logging.LogRecord):
    """Append extra->context to logs
    NOTE: This will appear in logs when used with logger.xxx(..., extra={'context': {..content}})
    """
    extra_str = ""
    custom_thread_name = ""
    if extra_raw := getattr(record, "context", None):
        extra_str = f" - EXTRA:{extra_raw!s}"
    if thread_name := getattr(record, "threadName", None):
        custom_thread_name = thread_name if thread_name != "MainThread" else "M"
    record.context = extra_str
    record.customThreadName = custom_thread_name
    return True


def log_extra(extra: dict[typing.Any, typing.Any]):
    """Basic helper function to view extra argument in logs using log_render_extra_context"""
    return {
        "context": extra,
    }


def log_extra_response(
    *,
    response: requests.Response,
    **kwargs: str | int | None,
):
    return log_extra(
        {
            **kwargs,
            "response": {
                "url": response.url,
                "status_code": response.status_code,
                "content": response.content,
            },
        },
    )
