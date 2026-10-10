"""The two pages of the app. app.py only routes between them; keeping the
pages in an importable module (no page-config or navigation side effects on
import) is what lets tests/test_ui.py run each page on its own.
"""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src" / "rag"))
sys.path.insert(0, str(ROOT / "src" / "scorecard"))

from errors import explain  # noqa: E402
from generate import generate_answer  # noqa: E402
from schema import SCORE_SCALE  # noqa: E402
from scope import OutOfScope  # noqa: E402
from score import score_feature  # noqa: E402

PRINCIPLE_LABELS = {
    "ahimsa": "Ahimsa · non-harm",
    "satya": "Satya · truthfulness",
    "dharma": "Dharma · accountability in context",
    "nyaya": "Nyaya · fairness and reasoning",
    "aparigraha": "Aparigraha · data minimization",
    "seva": "Seva · serving the user",
    "viveka": "Viveka · human oversight",
}

EXAMPLE_FEATURE = (
    "A retail-store camera system that uses facial recognition to identify known "
    "shoplifters and alert staff. Faces of all shoppers are scanned and stored for "
    "90 days. Staff see only a match alert with a confidence percentage."
)

MAX_INPUT_CHARS = 1500  # also caps what a stranger can make the free-tier APIs process


def score_colour(score: int) -> str:
    return "red" if score <= 2 else "orange" if score == 3 else "green"


def render_assistant(msg: dict) -> None:
    if msg.get("error"):
        st.error(msg["content"])
        return
    st.markdown(msg["content"])
    if msg.get("principles"):
        st.caption("Principles detected in your question: " + ", ".join(msg["principles"]))
    if msg.get("sources"):
        with st.expander(f"Sources ({len(msg['sources'])})"):
            for s in msg["sources"]:
                st.markdown(f"**[{s['n']}]** {s['source_label']}, {s['reference']}")
                st.caption(f"“{s['quote']}”")


def ask_page() -> None:
    st.title("Viveka 🪔")
    st.caption(
        "Ask about the ethics of an AI system or feature. Answers are grounded in "
        "passages from the Bhagavad Gita, the Yoga Sutras and the Upanishads, and "
        "cite them. These texts are used as analogy, not as engineering instruction."
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                render_assistant(msg)
            else:
                st.markdown(msg["content"])

    if prompt := st.chat_input(
        "e.g. Should a hiring algorithm explain its decisions to applicants?",
        max_chars=MAX_INPUT_CHARS,
    ):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching the texts and thinking (the free tier can add up to a minute)..."):
                try:
                    result = generate_answer(prompt)
                    reply = {
                        "role": "assistant",
                        "content": result["answer"],
                        "principles": result["detected_principles"],
                        "sources": result["sources"],
                    }
                except Exception as exc:
                    reply = {"role": "assistant", "content": explain(exc), "error": True}
            render_assistant(reply)
        st.session_state.messages.append(reply)


def render_scorecard(description: str, result: dict) -> None:
    card = result["scorecard"]
    st.divider()
    st.caption("Scored description: " + description)
    st.markdown(f"**Summary.** {card['overall_summary']}")
    st.caption(
        "Scores can change from one run to the next on the same description. Read the "
        "quoted evidence and the reasoning, not just the number, and treat this as a "
        "starting point for a human review rather than a verdict."
    )

    chart = pd.DataFrame(
        {"score (1-5)": [s["score"] for s in card["scores"]]},
        index=[s["principle"].capitalize() for s in card["scores"]],
    )
    st.bar_chart(chart, horizontal=True, sort=False)

    for s in card["scores"]:
        label = f":{score_colour(s['score'])}[{s['score']}/5]  {PRINCIPLE_LABELS[s['principle']]}"
        with st.expander(label, expanded=s["score"] <= 2):
            if s["evidence"].strip().lower() == "none stated":
                st.markdown("**Based on:** nothing in the description speaks to this, so it scores 3.")
            else:
                st.markdown(f"**Based on:** “{s['evidence']}”")
            st.markdown(f"**Why:** {s['rationale']}")
            st.markdown(f"**Suggested change:** {s['mitigation']}")


def audit_page() -> None:
    st.title("Audit a feature")
    st.caption(
        "Describe an AI feature. Viveka scores it from 1 to 5 on seven principles "
        "from classical Indian ethics. Each score quotes the exact words of your "
        "description it is based on; where the description is silent the score is 3. "
        "Scale: " + "; ".join(f"{k} = {v.split(' — ')[0].lower()}" for k, v in SCORE_SCALE.items()) + "."
    )

    description = st.text_area(
        "Feature description (this is an example, replace it)",
        value=EXAMPLE_FEATURE,
        height=140,
        max_chars=MAX_INPUT_CHARS,
    )

    if st.button("Score this feature", type="primary"):
        if not description.strip():
            st.warning("Describe a feature first, then press the button.")
        else:
            with st.spinner("Scoring against the seven principles (about 20 seconds, longer if the free tier is busy)..."):
                try:
                    result = score_feature(description)
                    st.session_state.audit = {"description": description, "result": result}
                except OutOfScope as e:
                    st.session_state.audit = {"description": description, "info": e.reply}
                except Exception as exc:
                    st.session_state.audit = {"description": description, "error": explain(exc)}

    audit = st.session_state.get("audit")
    if not audit:
        return
    if audit.get("error"):
        st.error(audit["error"])
    elif audit.get("info"):
        st.info(audit["info"])
    else:
        render_scorecard(audit["description"], audit["result"])
