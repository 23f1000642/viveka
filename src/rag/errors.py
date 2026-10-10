"""Turn the failures this app can hit into short messages for a user.

A raw traceback in a public demo is bad twice over: it is unreadable to the
person who triggered it, and it shows file paths and code. `explain()` logs
the full exception for whoever runs the server and returns one plain
sentence for the person using the app.

The two exception classes exist so callers can say what went wrong without
this module having to match on error-message text, which breaks the moment a
message is reworded.
"""
import logging

import requests

log = logging.getLogger("viveka")


class ConfigError(RuntimeError):
    """A required API key is missing."""


class ScorecardInvalid(ValueError):
    """The model never produced a scorecard that passed validation."""


BUSY = (
    "The free AI service this demo runs on is busy or rate-limited right now. "
    "Please wait about a minute and try again."
)
TIMEOUT = "The AI service took too long to respond. Please try again."
UNREACHABLE = "Couldn't reach the AI service. Check your internet connection and try again."
SERVICE_DOWN = "The AI service is having problems on its side. Please try again in a few minutes."
NOT_CONFIGURED = "This demo isn't set up correctly right now (a service key is missing or was rejected)."
BAD_SCORECARD = (
    "The model couldn't produce a valid scorecard this time. Try again, or reword the description."
)
GENERIC = "Something went wrong on our side. Please try again."


def explain(exc: Exception) -> str:
    log.error("request failed: %r", exc, exc_info=exc)

    # ConnectTimeout is both a Timeout and a ConnectionError: check Timeout first.
    if isinstance(exc, requests.exceptions.Timeout):
        return TIMEOUT
    if isinstance(exc, requests.exceptions.ConnectionError):
        return UNREACHABLE
    if isinstance(exc, requests.exceptions.HTTPError):
        status = exc.response.status_code if exc.response is not None else None
        if status == 429:
            return BUSY
        if status in (401, 403):
            return NOT_CONFIGURED
        if status is not None and status >= 500:
            return SERVICE_DOWN
        return GENERIC
    if isinstance(exc, ConfigError):
        return NOT_CONFIGURED
    if isinstance(exc, ScorecardInvalid):
        return BAD_SCORECARD
    return GENERIC
