"""The one place that knows which LLM provider this project talks to.
generate.py, scope.py and the scorecard all call the same chat endpoint, and
the model name has already gone stale once, so URL, model and API-key lookup
live here and nowhere else.
"""
import os

from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api.groq.com/openai/v1/chat/completions"
# Groq's free-tier model catalog changes over time — verify against
# GET https://api.groq.com/openai/v1/models before assuming a model name
# still exists. "llama-3.3-70b-versatile" 404'd; gpt-oss-120b is current.
MODEL = "openai/gpt-oss-120b"


def api_key() -> str:
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError(
            "GROQ_API_KEY not set. Create a free key at https://console.groq.com/ "
            "and add it to .env as GROQ_API_KEY=... (see .env.example)."
        )
    return key
