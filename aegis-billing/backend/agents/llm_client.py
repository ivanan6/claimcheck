"""
Tanak wrapper oko Google Gen AI SDK-a (Gemini). Svi agenti idu kroz ovaj klijent.

Ako je MOCK_MODE=true u .env-u, agenti uopste ne pozivaju Gemini API -
umesto toga vracaju pripremljene odgovore iz mock_responses.py. To
omogucava demo bez API kljuca (ako nesto pukne uzivo na pitch-u).

Gemini ima native JSON mode (response_mime_type='application/json') koji
garantuje validan JSON - mnogo cisce nego defenzivno parsiranje.
"""
import json
import os
from typing import Any

_client = None  # lazy init


def is_mock_mode() -> bool:
    """True ako je u .env-u MOCK_MODE=true (case-insensitive)."""
    return os.getenv("MOCK_MODE", "false").strip().lower() in ("1", "true", "yes", "on")


def get_client():
    """Lazy konstrukcija Gemini klijenta. Nikad se ne zove u mock modu."""
    global _client
    if _client is None:
        from google import genai  # lazy import

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY nije postavljen. Ili dodajte kljuc u .env "
                "(dobijate ga na https://aistudio.google.com/apikey), "
                "ili postavite MOCK_MODE=true."
            )
        _client = genai.Client(api_key=api_key)
    return _client


def get_model() -> str:
    return os.getenv("AEGIS_MODEL", "gemini-2.0-flash")


def call_json(system_prompt: str, user_prompt: str, max_tokens: int = 2048) -> Any:
    """
    Poziva Gemini sa zahtevom za JSON output. Vraca parsirani Python objekat.
    Koristi native JSON mode pa nije potrebno defenzivno parsiranje.
    """
    from google.genai import types

    client = get_client()
    resp = client.models.generate_content(
        model=get_model(),
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            max_output_tokens=max_tokens,
            temperature=0.2,  # niska temperatura za predvidive medicinske/pravne odgovore
        ),
    )

    raw = (resp.text or "").strip()
    if not raw:
        raise ValueError("Prazan odgovor od Gemini modela.")

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        # Veoma malo verovatno sa response_mime_type=application/json,
        # ali za svaki slucaj fallback na manuelnu ekstrakciju.
        for start_char, end_char in [("[", "]"), ("{", "}")]:
            start = raw.find(start_char)
            end = raw.rfind(end_char)
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(raw[start : end + 1])
                except json.JSONDecodeError:
                    continue
        raise ValueError(
            f"Nije moguce parsirati JSON odgovor:\n{raw[:500]}\nGreska: {e}"
        )
