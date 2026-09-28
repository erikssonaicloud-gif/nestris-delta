# NESTRIS Δ

4D falling-block puzzle / transdimensional density survival.  
**Lineage:** successor to [NESTRIS 3D](../nestris-3d/). Pieces are **ternary mated hypercubes** (A ⊗ B ⊗ C of classic tetrominoes). Survive by hyper-densifying across phase (w).

## Status

| Milestone | State |
|-----------|--------|
| **M0** P0 lattice + TMP + census | Done |
| **M1** Precomputed piece table | **Done** (stable full-space IDs) |
| M2 HyperWell collision (runtime) | P0 stub exists |
| M3 Triple-bag randomizer | Next |
| M7 Brane renderer | Not started |

## M1 — Stable ID freeze

**Always use the full 35-solid ID space (0–34).**  
Enumerating pure-only renumbers every solid (REACTOR becomes 13 instead of 18). Do not ship pure-only IDs.

| Tier | Count | IDs | Role |
|------|-------|-----|------|
| **Playable (pure tetromino)** | 30 | see `playable_ids` | Shape bag |
| **Catalyst (monomino-derived)** | 5 | `0, 1, 2, 7, 14` | Optional/debug — **not** game legendaries |
| **Named legendaries (spec §3.6)** | 4 | below | Guaranteed bag injection |

| Named legendary | ID | V | Symmetry |
|-----------------|----|---|----------|
| MONOLITH-Δ | **6** | 4 | 4 |
| REACTOR-Δ | **18** | 16 | 1 |
| HYPERCRADLE | **30** | 28 | 8 |
| PLATE-Δ | **34** | 64 | 4 |

Phase bags among playable (canonical `dims[3]` / w-extent): thin 9 / true 4 / hyper 17.

### Engine modules

| File | Role |
|------|------|
| `engine/nestris_delta_m1_engine.py` | **Primary M1** — `PieceTable`, `PIECE_TABLE`, export |
| `engine/nestris_delta_p0_v02.py` | P0 lattice + TMP + HyperWell stub |
| `engine/piece_table.py` | Compat shim (`cells` + size-class expansion) |
| `engine/data/piece_table_v1.json` | Compact freeze (~160 KB) — preferred runtime load |
| `engine/data/piece_table_35.json` | Verbose full export (stable IDs) |
| `engine/data/piece_table_30.json` | Pure subset export — **same full-space IDs** |

### Usage

```python
import sys
sys.path.insert(0, "engine")
from nestris_delta_m1_engine import PIECE_TABLE

# HYPERCRADLE at group rotation 0 (0..191)
cells = PIECE_TABLE.get_cells(30, 0)
# or
cells = PIECE_TABLE.get_cells(PIECE_TABLE.legendary_id("HYPERCRADLE"), 0)

thin_playable = [i for i in PIECE_TABLE.thin_ids if i in PIECE_TABLE.playable_ids]

# Fast load without recomputing census
from nestris_delta_m1_engine import PieceTable
pt = PieceTable.from_json("engine/data/piece_table_v1.json")
```

Size-class subcell expansion (½ / 1× / 2×):

```python
from piece_table import PieceTableCompat
pt = PieceTableCompat()
cells = pt.cells(18, 0, size_class="normal")  # REACTOR, 16×16 subcells
```

## Quick verify

```bash
cd ~/nestris-delta
python3 engine/nestris_delta_m1_engine.py   # rebuild freezes
python3 engine/nestris_delta_p0_v02.py
python3 tests/test_m1_engine.py
python3 tests/test_m1_piece_table.py
python3 tests/test_p0_census.py
```

## Layout

```
nestris-delta/
  engine/
    nestris_delta_m1_engine.py
    nestris_delta_p0_v02.py
    piece_table.py
    data/piece_table_v1.json
    data/piece_table_35.json
    data/piece_table_30.json
  ai/                     # SpaceXAI (xAI) client + piece oracle
  census/
  blueprint/
  docs/
  tests/
  requirements.txt
  .env.example
  README.md
```

## Source artifacts (Downloads)

Integrated from:

- `nestris_delta_m1_engine.py`, `test_m1_engine.py`
- `piece_table_30.json`, `piece_table_35.json` (regenerated with stable IDs)
- `nestris_delta_p0_v02.py`, Δ / 3D specs

**Correction vs Downloads notes:** monomino-derived IDs are **catalyst** tier, not game legendaries. Named legendaries are MONOLITH / REACTOR / HYPERCRADLE / PLATE.

## Next (M3)

Triple-bag randomizer over `playable_ids` + phase bags + named-legendary injection. M2 HyperWell stub already in P0.

## AI (SpaceXAI / xAI)

Default LLM provider is **SpaceXAI** (OpenAI-compatible xAI API). No other vendor wired in.

| Item | Value |
|------|--------|
| Env key | `XAI_API_KEY` |
| Base URL | `https://api.x.ai/v1` |
| Model | `grok-4.5` |
| Package | `ai/` — client + piece oracle |

```bash
# once
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
export XAI_API_KEY=...   # https://console.x.ai  (or copy .env.example → .env)

# offline: dump the context the oracle sends
.venv/bin/python -m ai --print-context

# live design / playtest Q&A (grounded in piece_table_v1_summary.json)
.venv/bin/python -m ai "How should the phase bag weight Thin vs Hyper for early playtest?"
.venv/bin/python -m ai --id 30
```

```python
from ai import PieceOracle, ask_grok

# Free-form Grok call
print(ask_grok("Say hello from NESTRIS Δ"))

# Piece-table-grounded coach
oracle = PieceOracle()
print(oracle.ask("Compare REACTOR-Δ and HYPERCRADLE for nesting hosts."))
```

Keep the key **server-side / env only** — never hardcode, never ship it in a browser bundle.

## Related

- 3D project: `~/nestris-3d/`
