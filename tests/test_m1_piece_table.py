"""M1 compat tests against piece_table shim (size-class expansion)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))

from nestris_delta_p0_v02 import TernaryMatingProduct as TMP, canonical_form
from piece_table import (
    DEFAULT_TABLE_PATH,
    PieceTableCompat,
    build_and_save,
    load_piece_table,
)


def test_frozen_table_loads():
    assert DEFAULT_TABLE_PATH.is_file()
    table = load_piece_table()
    pt = PieceTableCompat(table=None, path=DEFAULT_TABLE_PATH)
    assert pt.piece_count == 35
    assert pt.legendary_id("HYPERCRADLE") == 30


def test_lookup_matches_mate3():
    pt = PieceTableCompat()
    rid = pt.legendary_id("REACTOR-Δ")
    cells = set(pt.cells(rid, 0, size_class="half"))
    expected = set(map(tuple, TMP.mate3("O", "O", "O")))
    assert canonical_form(cells) == canonical_form(expected)


def test_size_scale_volume():
    pt = PieceTableCompat()
    rid = pt.legendary_id("REACTOR-Δ")
    assert len(pt.cells(rid, 0, "half")) == 16
    assert len(pt.cells(rid, 0, "normal")) == 16 * 16
    assert len(pt.cells(rid, 0, "double")) == 16 * 256


def test_translated_cells():
    pt = PieceTableCompat()
    rid = pt.legendary_id("MONOLITH-Δ")
    cells = pt.translated_cells(rid, 0, (1, 2, 3, 4), "half")
    base = pt.cells(rid, 0, "half")
    assert cells == [(x + 1, y + 2, z + 3, w + 4) for x, y, z, w in base]


def test_phase_bags_partition_playable():
    pt = PieceTableCompat()
    bags = pt.phase_bags
    merged = sorted(bags["thin"] + bags["true"] + bags["hyper"])
    assert merged == sorted(pt.playable_ids)


def test_rebuild():
    table, path = build_and_save()
    assert path.is_file()
    assert table["piece_count"] == 35
    assert table["legendaries"]["REACTOR-Δ"] == 18


if __name__ == "__main__":
    test_frozen_table_loads()
    test_lookup_matches_mate3()
    test_size_scale_volume()
    test_translated_cells()
    test_phase_bags_partition_playable()
    test_rebuild()
    print("All M1 compat tests passed.")
