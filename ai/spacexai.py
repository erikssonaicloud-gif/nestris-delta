"""
SpaceXAI client for NESTRIS Δ.

Provider name: SpaceXAI
Served by: xAI API (OpenAI-compatible)

  XAI_API_KEY   — required
  XAI_BASE_URL  — default https://api.x.ai/v1
  XAI_MODEL     — default grok-4.5

Docs: https://docs.x.ai/developers/quickstart
"""
from __future__ import annotations

import os
from typing import Any

# Defaults match current xAI docs (docs.x.ai). Override via env if names change.
DEFAULT_BASE_URL = "https://api.x.ai/v1"
DEFAULT_MODEL = "grok-4.5"


def get_model() -> str:
    return os.environ.get("XAI_MODEL", DEFAULT_MODEL)


def get_base_url() -> str:
    return os.environ.get("XAI_BASE_URL", DEFAULT_BASE_URL)


def get_api_key() -> str:
    key = os.environ.get("XAI_API_KEY")
    if not key:
        raise RuntimeError(
            "XAI_API_KEY is not set. Create a key at https://console.x.ai "
            "and export it (or put it in a git-ignored .env)."
        )
    return key


def get_client():
    """OpenAI-compatible client pointed at SpaceXAI / xAI."""
    from openai import OpenAI

    return OpenAI(api_key=get_api_key(), base_url=get_base_url())


def ask_grok(
    input_text: str,
    *,
    model: str | None = None,
    instructions: str | None = None,
    **kwargs: Any,
) -> str:
    """
    One-shot Responses API call. Returns output text.

    Keeps the key server-side (env only). Never pass keys from a browser bundle.
    """
    client = get_client()
    model = model or get_model()
    params: dict[str, Any] = {
        "model": model,
        "input": input_text,
    }
    if instructions:
        params["instructions"] = instructions
    params.update(kwargs)
    resp = client.responses.create(**params)
    text = getattr(resp, "output_text", None)
    if text:
        return text
    # Fallback if SDK shape differs
    return str(resp)
