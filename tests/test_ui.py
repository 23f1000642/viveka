"""Run each page headlessly with the network calls replaced by stubs, and
check what a user would actually see. The point is the unhappy paths: a
rate-limit must show one plain sentence, never a traceback."""
from types import SimpleNamespace

import requests
from streamlit.testing.v1 import AppTest

import errors
import ui
from schema import PRINCIPLES
from scope import OutOfScope


def chat_script():
    from ui import ask_page

    ask_page()


def audit_script():
    from ui import audit_page

    audit_page()


def rate_limited(*_):
    raise requests.exceptions.HTTPError(response=SimpleNamespace(status_code=429))


def ask(question="Should a hiring algorithm explain itself?"):
    at = AppTest.from_function(chat_script, default_timeout=30).run()
    at.chat_input[0].set_value(question).run()
    return at


def press_score(text=None):
    at = AppTest.from_function(audit_script, default_timeout=30).run()
    if text is not None:
        at.text_area[0].set_value(text)
    at.button[0].click().run()
    return at


def valid_result(scores=(1, 3, 4, 3, 2, 3, 3)):
    return {
        "feature": "x",
        "attempts": 1,
        "sources": [],
        "scorecard": {
            "overall_summary": "A short summary.",
            "scores": [
                {"principle": p, "evidence": "none stated" if s == 3 else "a quote", "score": s,
                 "rationale": f"why {p}", "mitigation": f"fix {p}"}
                for p, s in zip(PRINCIPLES, scores)
            ],
        },
    }


# ---- chat page ----

def test_chat_rate_limit_shows_one_plain_message(monkeypatch):
    monkeypatch.setattr(ui, "generate_answer", rate_limited)
    at = ask()
    assert not at.exception
    assert [e.value for e in at.error] == [errors.BUSY]


def test_chat_error_stays_in_the_history_on_the_next_rerun(monkeypatch):
    monkeypatch.setattr(ui, "generate_answer", rate_limited)
    at = ask()
    at.run()
    assert not at.exception
    assert [e.value for e in at.error] == [errors.BUSY]


def test_chat_unexpected_exception_is_generic_not_a_traceback(monkeypatch):
    def broken(*_):
        raise KeyError("choices")

    monkeypatch.setattr(ui, "generate_answer", broken)
    at = ask()
    assert not at.exception
    assert [e.value for e in at.error] == [errors.GENERIC]


def test_chat_success_shows_answer_and_sources(monkeypatch):
    monkeypatch.setattr(ui, "generate_answer", lambda q: {
        "answer": "Verdict: yes.",
        "detected_principles": ["nyaya"],
        "sources": [{"n": 1, "source_label": "Katha", "reference": "Katha Upanishad", "quote": "a quote"}],
    })
    at = ask()
    assert not at.exception and not at.error
    assert any("Verdict: yes." in m.value for m in at.markdown)
    assert [e.label for e in at.expander] == ["Sources (1)"]


# ---- audit page ----

def test_audit_empty_description_warns_and_calls_nothing(monkeypatch):
    called = []
    monkeypatch.setattr(ui, "score_feature", lambda d: called.append(d))
    at = press_score("   ")
    assert not at.exception
    assert len(at.warning) == 1 and not called


def test_audit_invalid_scorecard_shows_plain_message(monkeypatch):
    def invalid(d):
        raise errors.ScorecardInvalid("after 3 attempts")

    monkeypatch.setattr(ui, "score_feature", invalid)
    at = press_score()
    assert not at.exception
    assert [e.value for e in at.error] == [errors.BAD_SCORECARD]


def test_audit_rate_limit_shows_plain_message(monkeypatch):
    monkeypatch.setattr(ui, "score_feature", rate_limited)
    at = press_score()
    assert not at.exception
    assert [e.value for e in at.error] == [errors.BUSY]


def test_audit_out_of_scope_shows_the_fixed_reply_not_a_scorecard(monkeypatch):
    def out_of_scope(d):
        raise OutOfScope("personal_distress", "That sounds really hard.")

    monkeypatch.setattr(ui, "score_feature", out_of_scope)
    at = press_score("I feel alone")
    assert not at.exception and not at.error
    assert [i.value for i in at.info] == ["That sounds really hard."]
    assert not at.expander


def test_audit_success_renders_seven_principles_and_opens_the_low_ones(monkeypatch):
    monkeypatch.setattr(ui, "score_feature", lambda d: valid_result())
    at = press_score()
    assert not at.exception and not at.error
    assert len(at.expander) == 7
    # scores (1, 3, 4, 3, 2, 3, 3): only ahimsa (1) and aparigraha (2) are <= 2
    assert [e.proto.expanded for e in at.expander] == [True, False, False, False, True, False, False]
