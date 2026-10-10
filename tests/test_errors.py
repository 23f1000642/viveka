from types import SimpleNamespace

import pytest
import requests

import errors


def http_error(status):
    return requests.exceptions.HTTPError(response=SimpleNamespace(status_code=status))


@pytest.mark.parametrize(
    "exc, expected",
    [
        (requests.exceptions.ReadTimeout(), errors.TIMEOUT),
        # ConnectTimeout is both a Timeout and a ConnectionError: must read as a timeout.
        (requests.exceptions.ConnectTimeout(), errors.TIMEOUT),
        (requests.exceptions.ConnectionError(), errors.UNREACHABLE),
        (http_error(429), errors.BUSY),
        (http_error(401), errors.NOT_CONFIGURED),
        (http_error(403), errors.NOT_CONFIGURED),
        (http_error(500), errors.SERVICE_DOWN),
        (http_error(503), errors.SERVICE_DOWN),
        (http_error(400), errors.GENERIC),
        (requests.exceptions.HTTPError(), errors.GENERIC),  # no response attached
        (errors.ConfigError("GROQ_API_KEY not set"), errors.NOT_CONFIGURED),
        (errors.ScorecardInvalid("still invalid"), errors.BAD_SCORECARD),
        (KeyError("choices"), errors.GENERIC),
        (IndexError(), errors.GENERIC),
    ],
)
def test_explain_maps_each_failure_to_one_plain_message(exc, expected):
    assert errors.explain(exc) == expected


def test_messages_never_leak_internals():
    leaky = ("Traceback", "api.groq.com", "voyageai", "GROQ_API_KEY", "File \"", ".py")
    for message in (errors.BUSY, errors.TIMEOUT, errors.UNREACHABLE, errors.SERVICE_DOWN,
                    errors.NOT_CONFIGURED, errors.BAD_SCORECARD, errors.GENERIC):
        assert not any(fragment in message for fragment in leaky), message


def test_explain_logs_the_real_exception_for_the_operator(caplog):
    with caplog.at_level("ERROR", logger="viveka"):
        errors.explain(KeyError("choices"))
    assert "KeyError" in caplog.text
