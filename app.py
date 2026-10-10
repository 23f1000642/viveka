import streamlit as st

from ui import ask_page, audit_page

st.set_page_config(page_title="Viveka", page_icon="🪔")

pages = [
    st.Page(ask_page, title="Ask a question", url_path="ask", default=True),
    st.Page(audit_page, title="Audit a feature", url_path="audit"),
]
st.navigation(pages).run()
