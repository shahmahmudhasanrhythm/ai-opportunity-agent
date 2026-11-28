"""One place to call Gemini, instead of the same 10 lines copied four times."""
from __future__ import annotations

import requests

from .config import GEMINI_MODELS

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def generate(contents, api_key: str, models: list[str] | None = None, timeout: int = 30) -> str | None:
    """Return the model's text, or None if every model failed.

    `contents` can be a plain prompt string or a list of chat turns
    ({"role": "user"|"model", "parts": [{"text": ...}]}).

    The API key goes in a header, not in the URL. URLs end up in logs,
    browser history and error messages; headers usually don't.
    """
    if isinstance(contents, str):
        contents = [{"parts": [{"text": contents}]}]
    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}

    for model in models or GEMINI_MODELS:
        try:
            response = requests.post(
                API_URL.format(model=model), json={"contents": contents}, headers=headers, timeout=timeout
            )
            if response.status_code == 200:
                return response.json()["candidates"][0]["content"]["parts"][0]["text"]
            # 429 (rate limit), 5xx (overloaded), 404 (model retired): try the next model
        except (requests.RequestException, KeyError, IndexError, ValueError):
            continue
    return None
