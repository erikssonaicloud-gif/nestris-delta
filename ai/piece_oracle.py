"""
Piece Oracle — Grok coach grounded in the frozen M1 piece table.

Use for design questions, taxonomy, legendary roles, bag balance, and
playtest strategy notes. Engine facts come from JSON / PieceTable, not
from model memory alone.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .spacexai import ask_grok, get_model

ROOT = Path(__file__).resolve().parent.parent
SUMMARY_PATH = ROOT / "engine" / "data" / "piece_table_v1_summary.json"

SYSTEM = """You are the NESTRIS Δ Piece Oracle — a design/playtest assistant for a
4D falling-block game. Pieces are ternary mated hypercubes (A ⊗ B ⊗ C of
classic tetrominoes I,O,T,L,Z, and monomino ".").

Hard rules:
- Always use the FULL 35-solid ID space (0–34). Never renumber pure-only.
- Playable bag: 30 pure-tetromino solids. Catalysts (monomino-derived IDs
  0,1,2,7,14) are optional/debug — NOT game legendaries.
- Named legendaries (stable IDs): MONOLITH-Δ=6, REACTOR-Δ=18, HYPERCRADLE=30, PLATE-Δ=34.
- Phase classes by max free-axis extent / w: Thin, True, Hyper.
- Prefer facts from the provided piece-table context. If something is not
  in context, say so rather than inventing IDs or volumes.
- Be concise, tactical, and specific (cite solid IDs and names).
"""


def load_summary(path: Path | None = None) -> dict[str, Any]:
    p = path or SUMMARY_PATH
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def format_context(summary: dict[str, Any], focus_ids: list[int] | None = None) -> str:
    """Compact context block for the model (full summary is small enough)."""
    legendaries = summary.get("legendaries", {})
    bags = summary.get("phase_bags", {})
    pieces = summary.get("pieces", [])

    lines = [
        f"Piece table version={summary.get('version')} count={summary.get('piece_count')} "
        f"playable={summary.get('playable_count')}",
        f"Playable IDs: {summary.get('playable_ids')}",
        f"Catalyst IDs: {summary.get('catalyst_ids')}",
        f"Legendaries: {legendaries}",
        f"Phase bags (playable): thin={bags.get('thin')} true={bags.get('true')} hyper={bags.get('hyper')}",
        "Solids:",
    ]

    for p in pieces:
        if focus_ids is not None and p["id"] not in focus_ids:
            continue
        named = p.get("named_legendary") or ""
        tag = f" [{named}]" if named else ""
        pure = "pure" if p.get("is_pure") else "catalyst"
        lines.append(
            f"  id={p['id']:2d} V={p['volume']:2d} dims={p['dims']} "
            f"w={p.get('w_class')} sym={p.get('symmetry_count')} "
            f"{pure} {p.get('canonical_name')}{tag}"
        )
    return "\n".join(lines)


class PieceOracle:
    """Grok-backed Q&A over the M1 piece table."""

    def __init__(
        self,
        summary: dict[str, Any] | None = None,
        summary_path: Path | None = None,
        model: str | None = None,
    ):
        self.summary = summary if summary is not None else load_summary(summary_path)
        self.model = model or get_model()
        self._context = format_context(self.summary)

    def ask(self, question: str, *, focus_ids: list[int] | None = None) -> str:
        ctx = format_context(self.summary, focus_ids) if focus_ids else self._context
        user = (
            f"## Frozen piece table context\n{ctx}\n\n"
            f"## Question\n{question}"
        )
        return ask_grok(user, model=self.model, instructions=SYSTEM)

    def describe_solid(self, solid_id: int) -> str:
        return self.ask(
            f"Explain solid id={solid_id}: geometry role, phase class, "
            f"when a player wants it, and how it relates to legendaries / nesting.",
            focus_ids=[solid_id],
        )


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in {"-h", "--help"}:
        print(
            "Usage:\n"
            "  python -m ai \"Why is HYPERCRADLE legendary?\"\n"
            "  python -m ai --id 18\n"
            "  python -m ai --print-context\n\n"
            "Requires XAI_API_KEY (SpaceXAI / xAI). See .env.example."
        )
        return 0

    if argv[0] == "--print-context":
        print(format_context(load_summary()))
        return 0

    # Lazy: only need API for live calls
    oracle = PieceOracle()

    if argv[0] == "--id" and len(argv) >= 2:
        print(oracle.describe_solid(int(argv[1])))
        return 0

    question = " ".join(argv)
    print(oracle.ask(question))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
