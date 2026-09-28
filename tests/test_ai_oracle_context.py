"""Offline tests for SpaceXAI piece-oracle scaffolding (no API key required)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ai.piece_oracle import format_context, load_summary  # noqa: E402
from ai.spacexai import DEFAULT_BASE_URL, DEFAULT_MODEL, get_model, get_base_url  # noqa: E402


def test_defaults():
    assert DEFAULT_MODEL == "grok-4.5"
    assert DEFAULT_BASE_URL == "https://api.x.ai/v1"
    assert get_model() == "grok-4.5"
    assert get_base_url() == "https://api.x.ai/v1"


def test_summary_loads_and_has_stable_legendaries():
    s = load_summary()
    assert s["piece_count"] == 35
    assert s["playable_count"] == 30
    legs = s["legendaries"]
    # Keys may be unicode Δ
    by_name = {k.replace("Δ", "Δ"): v for k, v in legs.items()}
    assert 6 in legs.values()  # MONOLITH
    assert 18 in legs.values()  # REACTOR
    assert 30 in legs.values()  # HYPERCRADLE
    assert 34 in legs.values()  # PLATE
    assert set(s["catalyst_ids"]) == {0, 1, 2, 7, 14}


def test_format_context_includes_ids():
    text = format_context(load_summary())
    assert "id=18" in text or "id=18 " in text
    assert "REACTOR" in text or "18" in text
    assert "playable=30" in text or "playable=30" in text.replace(" ", "")
    assert "HYPERCRADLE" in text or "id=30" in text


def test_focus_filter():
    text = format_context(load_summary(), focus_ids=[18])
    assert "id=18" in text
    # Should not dump every solid line
    assert text.count("\n  id=") == 1


if __name__ == "__main__":
    test_defaults()
    test_summary_loads_and_has_stable_legendaries()
    test_format_context_includes_ids()
    test_focus_filter()
    print("ok")
