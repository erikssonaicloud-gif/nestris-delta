"""
Compatibility shim — prefer `nestris_delta_m1_engine`.

Re-exports PieceTable API and provides the older `cells()` / size-class helpers
used by early M1 notes.
"""
from __future__ import annotations

from pathlib import Path

from nestris_delta_m1_engine import (
    DATA_DIR,
    DEFAULT_COMPACT,
    PIECE_TABLE,
    PIECE_TABLE_FULL,
    PieceTable,
    rebuild_and_export,
)

DEFAULT_TABLE_PATH = DEFAULT_COMPACT
TABLE_VERSION = 1


class PieceTableCompat(PieceTable):
    """Adds size-class expansion helpers on top of M1 PieceTable."""

    SIZE_SCALE = {"half": 1, "normal": 2, "double": 4, 0.5: 1, 1: 2, 2: 4}

    def __init__(self, table=None, path=None, build: bool = False):
        if table is not None or path is not None:
            # load path
            p = path or DEFAULT_TABLE_PATH
            loaded = PieceTable.from_json(p)
            self.__dict__.update(loaded.__dict__)
        elif build:
            super().__init__(build=True)
        else:
            # default: share global freeze
            self.__dict__.update(PIECE_TABLE.__dict__)

    @property
    def piece_count(self) -> int:
        return len(self.solids)

    def meta(self, canonical_id: int):
        return self.by_id[canonical_id]

    def cells(self, canonical_id, rotation_idx=0, size_class="normal"):
        base = self.get_cells(canonical_id, rotation_idx)
        scale = self.SIZE_SCALE.get(size_class, int(size_class) if size_class not in self.SIZE_SCALE else 1)
        if scale == 1:
            return base
        out = []
        for cx, cy, cz, cw in base:
            for dx in range(scale):
                for dy in range(scale):
                    for dz in range(scale):
                        for dw in range(scale):
                            out.append(
                                (cx * scale + dx, cy * scale + dy, cz * scale + dz, cw * scale + dw)
                            )
        return out

    def translated_cells(self, canonical_id, rotation_idx, position, size_class="normal"):
        ox, oy, oz, ow = position
        return [
            (x + ox, y + oy, z + oz, w + ow)
            for x, y, z, w in self.cells(canonical_id, rotation_idx, size_class)
        ]

    @property
    def legendaries(self):
        return dict(self.named_legendaries)

    @property
    def phase_bags(self):
        return {
            "thin": [i for i in self.thin_ids if i in self.playable_ids],
            "true": [i for i in self.true_ids if i in self.playable_ids],
            "hyper": [i for i in self.hyper_ids if i in self.playable_ids],
        }


def load_piece_table(path=None):
    return PieceTable.from_json(path or DEFAULT_TABLE_PATH)


def build_piece_table():
    return PieceTable().to_compact_json()


def save_piece_table(table, path=None):
    """Persist compact table dict (or rebuild from live PieceTable)."""
    path = Path(path or DEFAULT_COMPACT)
    if isinstance(table, dict):
        path.parent.mkdir(parents=True, exist_ok=True)
        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump(table, f, separators=(",", ":"))
        return path
    return table.save_compact(path)


def build_and_save(path=None):
    pt = PieceTable()
    out = pt.save_compact(path or DEFAULT_COMPACT)
    return pt.to_compact_json(), out


if __name__ == "__main__":
    rebuild_and_export()
