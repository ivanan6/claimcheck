"""
Thin wrapper around the LLM provider. All agents go through this client.

The provider is selected through the LLM_PROVIDER env var:
  - "gemini"  (default) -> Google Gen AI SDK
  - "ollama"            -> local Ollama instance (e.g. llama3.2)

If MOCK_MODE=true in .env, agents do not call the LLM and return prepared
responses from mock_responses.py instead.

Both providers use native JSON mode, so defensive parsing should rarely be needed.
"""
import json
import os
import re
import time
from typing import Any

_client = None  # lazy init

# Number of retries if Gemini returns 429 (RESOURCE_EXHAUSTED).
_MAX_RETRIES = int(os.getenv("AEGIS_LLM_MAX_RETRIES", "5"))
# Fallback delay if Gemini does not send retryDelay in the response.
_DEFAULT_RETRY_SECONDS = int(os.getenv("AEGIS_LLM_DEFAULT_RETRY_SECONDS", "30"))
# Upper delay limit per attempt to avoid blocking forever.
_MAX_RETRY_SECONDS = int(os.getenv("AEGIS_LLM_MAX_RETRY_SECONDS", "120"))


def _extract_retry_seconds(err: Exception) -> int:
    """Read retryDelay from a Gemini ClientError. Returns seconds with a small buffer."""
    text = str(err)
    match = re.search(r"retryDelay['\"]?\s*:\s*['\"]?(\d+(?:\.\d+)?)s", text)
    if match:
        seconds = float(match.group(1))
    else:
        seconds = _DEFAULT_RETRY_SECONDS
    return min(int(seconds) + 2, _MAX_RETRY_SECONDS)


def _is_rate_limit(err: Exception) -> bool:
    """True if this is 429/RESOURCE_EXHAUSTED from the Gemini SDK."""
    code = getattr(err, "code", None)
    if code == 429:
        return True
    text = str(err)
    return "429" in text or "RESOURCE_EXHAUSTED" in text


def is_mock_mode() -> bool:
    """True if MOCK_MODE=true in .env (case-insensitive)."""
    return os.getenv("MOCK_MODE", "false").strip().lower() in ("1", "true", "yes", "on")


def get_client():
    """Lazy Gemini client construction. Never called in mock mode."""
    global _client
    if _client is None:
        from google import genai  # lazy import

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add the key to .env "
                "(get it at https://aistudio.google.com/apikey), "
                "or set MOCK_MODE=true."
            )
        _client = genai.Client(api_key=api_key)
    return _client


def get_provider() -> str:
    """'ollama' for a local Llama, otherwise 'gemini'."""
    return os.getenv("LLM_PROVIDER", "gemini").strip().lower()


def get_model() -> str:
    """Default model depends on the provider."""
    explicit = os.getenv("AEGIS_MODEL")
    if explicit:
        return explicit
    return "llama3.2" if get_provider() == "ollama" else "gemini-2.0-flash"


def _call_ollama_json(system_prompt: str, user_prompt: str, max_tokens: int) -> Any:
    """Call local Ollama (http://localhost:11434/api/chat) with format='json'."""
    import requests  # already present as a transitive dependency of google-genai

    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    timeout_s = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120"))

    payload = {
        "model": get_model(),
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": max_tokens,
        },
    }

    try:
        r = requests.post(f"{base_url}/api/chat", json=payload, timeout=timeout_s)
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(
            f"Cannot connect to Ollama ({base_url}). "
            f"Start it with 'ollama serve' and check whether model "
            f"'{get_model()}' exists ('ollama list'). Details: {e}"
        )

    if r.status_code != 200:
        raise RuntimeError(f"Ollama error {r.status_code}: {r.text[:400]}")

    data = r.json()
    content = (data.get("message") or {}).get("content", "").strip()
    if not content:
        raise ValueError("Empty response from the Ollama model.")

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        repaired = _repair_json_prefix(content)
        if repaired is not None:
            return repaired
        # Fallback - try to find the first JSON array/object in the string.
        for start_char, end_char in [("[", "]"), ("{", "}")]:
            start = content.find(start_char)
            end = content.rfind(end_char)
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(content[start : end + 1])
                except json.JSONDecodeError:
                    continue
        raise ValueError(
            f"Cannot parse Ollama JSON response:\n{content[:500]}\nError: {e}"
        )


def _repair_json_prefix(content: str) -> Any | None:
    """Parse the largest complete JSON prefix from a truncated local model response."""
    starts = [idx for idx in (content.find("["), content.find("{")) if idx != -1]
    if not starts:
        return None

    start = min(starts)
    opening = content[start]
    closing = "]" if opening == "[" else "}"
    stack: list[str] = []
    in_string = False
    escaped = False
    last_complete = -1

    for index, char in enumerate(content[start:], start=start):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char in "[{":
            stack.append("]" if char == "[" else "}")
        elif char in "]}":
            if not stack or stack[-1] != char:
                break
            stack.pop()
            if not stack and char == closing:
                last_complete = index + 1

    if last_complete == -1:
        return None

    candidate = content[start:last_complete]
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None

    if isinstance(parsed, dict):
        for key in ("issues", "problems", "errors"):
            value = parsed.get(key)
            if isinstance(value, list):
                return value
    return parsed


def call_json(system_prompt: str, user_prompt: str, max_tokens: int = 2048) -> Any:
    """
    Call the selected LLM with a JSON output request. Returns a parsed Python object.
    """
    if get_provider() == "ollama":
        return _call_ollama_json(system_prompt, user_prompt, max_tokens)

    from google.genai import types

    client = get_client()
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        response_mime_type="application/json",
        max_output_tokens=max_tokens,
        temperature=0.2,  # low temperature for predictable medical/legal responses
    )

    resp = None
    last_err: Exception | None = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            resp = client.models.generate_content(
                model=get_model(),
                contents=user_prompt,
                config=config,
            )
            break
        except Exception as err:  # google.genai.errors.ClientError i sl.
            if not _is_rate_limit(err) or attempt == _MAX_RETRIES:
                raise
            wait_s = _extract_retry_seconds(err)
            print(
                f"[llm_client] Gemini 429 (attempt {attempt}/{_MAX_RETRIES}). "
                f"Waiting {wait_s}s before retrying...",
                flush=True,
            )
            time.sleep(wait_s)
            last_err = err

    if resp is None:
        # Defensive - should not happen because the loop either breaks or raises.
        raise last_err or RuntimeError("Gemini call failed without a clear reason.")

    raw = (resp.text or "").strip()
    if not raw:
        raise ValueError("Empty response from the Gemini model.")

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        # Very unlikely with response_mime_type=application/json, but keep a
        # fallback to manual extraction just in case.
        for start_char, end_char in [("[", "]"), ("{", "}")]:
            start = raw.find(start_char)
            end = raw.rfind(end_char)
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(raw[start : end + 1])
                except json.JSONDecodeError:
                    continue
        raise ValueError(
            f"Cannot parse JSON response:\n{raw[:500]}\nError: {e}"
        )
