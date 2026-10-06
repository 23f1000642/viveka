import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src" / "rag"))

from generate import generate_answer  # noqa: E402

st.set_page_config(page_title="Viveka", page_icon="🪔")
st.title("Viveka 🪔")
st.caption(
    "Ask about the ethics of an AI system or feature. Answers are grounded in "
    "passages from the Bhagavad Gita, the Yoga Sutras and the Upanishads, and "
    "cite them. These texts are used as analogy, not as engineering instruction."
)

if "messages" not in st.session_state:
    st.session_state.messages = []


def render_assistant(msg: dict) -> None:
    st.markdown(msg["content"])
    if msg.get("principles"):
        st.caption("Principles detected in your question: " + ", ".join(msg["principles"]))
    if msg.get("sources"):
        with st.expander(f"Sources ({len(msg['sources'])})"):
            for s in msg["sources"]:
                where = f"{s['source_label']}" + (f", {s['book']}" if s["book"] else "")
                st.markdown(f"**[{s['n']}]** {where}, verse(s) {s['verses']}")
                st.caption(f"“{s['quote']}”")


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            render_assistant(msg)
        else:
            st.markdown(msg["content"])

if prompt := st.chat_input("e.g. Should a hiring algorithm explain its decisions to applicants?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Searching the texts and thinking..."):
            result = generate_answer(prompt)
        reply = {
            "role": "assistant",
            "content": result["answer"],
            "principles": result["detected_principles"],
            "sources": result["sources"],
        }
        render_assistant(reply)
    st.session_state.messages.append(reply)
