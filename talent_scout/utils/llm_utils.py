import json
import os
import re
import threading

from google import genai

from config import GEMINI_MODEL

_client = None
_client_lock = threading.Lock()


def get_gemini_client():
    """Create the Gemini client on first use so a missing key doesn't break imports."""
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    raise RuntimeError(
                        "GEMINI_API_KEY is not set. Add it to your environment or to a .env file."
                    )
                _client = genai.Client(api_key=api_key)
    return _client


def parse_json_response(text: str):
    """Parse an LLM JSON response, tolerating markdown fences or surrounding prose."""
    if text is None:
        raise ValueError("Empty response from LLM.")
    cleaned = text.strip()
    fenced = re.match(r"^```(?:json)?\s*(.*?)\s*```$", cleaned, re.DOTALL | re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(1)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start != -1 and end > start:
            return json.loads(cleaned[start:end + 1])
        raise


def generate_json(prompt: str, client=None, model: str = None):
    """Call Gemini in JSON mode and return the parsed response."""
    client = client or get_gemini_client()
    response = client.models.generate_content(
        model=model or GEMINI_MODEL,
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )
    return parse_json_response(response.text)
