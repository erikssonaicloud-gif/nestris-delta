"""
NESTRIS Δ — M1 Test Suite
Run: python3 tests/test_m1_engine.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))

from nestris_delta_m1_engine import (
    PIECE_TABLE,
    PIECE_TABLE_FULL,
    ROTATIONS_192,
    TernaryMatingProduct,
    bbox,
    canonical_form,
    PieceTable,
    transform_cells,
)


class TestRotationGroup:
    def test_order_192(self):
        assert len(ROTATIONS_192) == 192

    def test_all_det_plus_one(self):
        for perm, signs in ROTATIONS_192:
            p_sign = (
                1
                if sum(1 for i in range(4) for j in range(i + 1, 4) if perm[i] > perm[j]) % 2
                == 0
                else -1
            )
            s_sign = 1
            for s in signs:
                s_sign *= s
            assert p_sign * s_sign == 1


class TestTernaryMating:
    def test_reactor_volume(self):
        cells = TernaryMatingProduct.mate3("O", "O", "O")
        assert len(cells) == 16
        assert bbox(cells) == (2, 2, 2, 2)

    def test_plate_volume(self):
        cells = TernaryMatingProduct.mate3("I", "I", "I")
        assert len(cells) == 64
        assert bbox(cells) == (4, 4, 1, 4)

    def test_hypercradle_volume(self):
        cells = TernaryMatingProduct.mate3("T", "T", "T")
        assert len(cells) == 28
        assert bbox(cells) == (3, 3, 2, 3)

    def test_hypercradle_overhang(self):
        cells = TernaryMatingProduct.mate3("T", "T", "T")
        by_z = {}
        for x, y, z, w in cells:
            by_z.setdefault(z, []).append((x, y, w))
        assert len(by_z[0]) == 27
        assert len(by_z[1]) == 1
        assert len(by_z[0]) - len(by_z[1]) == 26


class TestPieceTable:
    def test_full_set_size(self):
        assert len(PIECE_TABLE.solids) == 35
        assert PIECE_TABLE is PIECE_TABLE_FULL

    def test_pure_set_size(self):
        assert len(PIECE_TABLE.pure_ids) == 30
        assert len(PIECE_TABLE.playable_ids) == 30

    def test_catalyst_ids(self):
        assert len(PIECE_TABLE.catalyst_ids) == 5
        assert set(PIECE_TABLE.catalyst_ids) == {0, 1, 2, 7, 14}
        # back-compat alias
        assert PIECE_TABLE.legendary_ids == PIECE_TABLE.catalyst_ids

    def test_id_stability(self):
        pt2 = PieceTable()
        for s1, s2 in zip(PIECE_TABLE.solids, pt2.solids):
            assert s1["id"] == s2["id"]
            assert s1["canonical_cells"] == s2["canonical_cells"]
            assert s1["volume"] == s2["volume"]

    def test_no_pure_only_renumber(self):
        """REACTOR must be 18 on full space, not 13 from pure-only sort."""
        assert PIECE_TABLE.named_legendaries["REACTOR-Δ"] == 18
        assert PIECE_TABLE.named_legendaries["HYPERCRADLE"] == 30
        assert PIECE_TABLE.named_legendaries["PLATE-Δ"] == 34
        assert PIECE_TABLE.named_legendaries["MONOLITH-Δ"] == 6

    def test_rotation_preserves_volume(self):
        for s in PIECE_TABLE.solids:
            vol = s["volume"]
            for ri in range(0, 192, 17):
                assert len(PIECE_TABLE.get_cells(s["id"], ri)) == vol
            assert len(s["rotations"]) == s["symmetry_count"]

    def test_unique_rotations(self):
        for s in PIECE_TABLE.solids:
            forms = [tuple(map(tuple, r)) for r in s["rotations"]]
            assert len(forms) == len(set(forms))

    def test_canonical_is_lexmin(self):
        for s in PIECE_TABLE.solids:
            canon = tuple(map(tuple, s["canonical_cells"]))
            forms = [tuple(map(tuple, r)) for r in s["rotations"]]
            assert canon == min(forms)

    def test_w_class_coverage(self):
        for s in PIECE_TABLE.solids:
            assert s["w_class"] in ("Thin", "True", "Hyper")
            if s["w_extent"] == 1:
                assert s["w_class"] == "Thin"
            elif s["w_extent"] == 2:
                assert s["w_class"] == "True"
            else:
                assert s["w_class"] == "Hyper"

    def test_pure_vs_catalyst_partition(self):
        assert len(PIECE_TABLE.pure_ids) == 30
        assert len(PIECE_TABLE.catalyst_ids) == 5
        assert set(PIECE_TABLE.pure_ids) & set(PIECE_TABLE.catalyst_ids) == set()
        assert set(PIECE_TABLE.pure_ids) | set(PIECE_TABLE.catalyst_ids) == set(range(35))

    def test_json_roundtrip(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        try:
            PIECE_TABLE.save_json(path)
            pt_loaded = PieceTable.from_json(path)
            assert len(pt_loaded.solids) == 35
            for s1, s2 in zip(PIECE_TABLE.solids, pt_loaded.solids):
                assert s1["id"] == s2["id"]
                assert s1["volume"] == s2["volume"]
                assert s1["symmetry_count"] == s2["symmetry_count"]
            assert pt_loaded.named_legendaries["REACTOR-Δ"] == 18
        finally:
            os.unlink(path)

    def test_get_cells_192_index(self):
        rid = PIECE_TABLE.legendary_id("REACTOR-Δ")
        c0 = PIECE_TABLE.get_cells(rid, 0)
        c42 = PIECE_TABLE.get_cells(rid, 42)
        assert len(c0) == 16
        assert len(c42) == 16
        # fully symmetric: all rotations identical
        assert set(c0) == set(c42)


class TestSignaturePieces:
    def test_reactor_in_table(self):
        reactor = next(s for s in PIECE_TABLE.solids if "(O,O,O)" in s["all_names"])
        assert reactor["id"] == 18
        assert reactor["volume"] == 16
        assert reactor["dims"] == (2, 2, 2, 2)
        assert reactor["w_class"] == "True"
        assert reactor["symmetry_count"] == 1

    def test_plate_in_table(self):
        plate = next(s for s in PIECE_TABLE.solids if "(I,I,I)" in s["all_names"])
        assert plate["id"] == 34
        assert plate["volume"] == 64
        assert plate["dims"] == (4, 4, 1, 4)
        assert plate["w_class"] == "Hyper"

    def test_hypercradle_in_table(self):
        cradle = next(s for s in PIECE_TABLE.solids if "(T,T,T)" in s["all_names"])
        assert cradle["id"] == 30
        assert cradle["volume"] == 28
        assert cradle["dims"] == (3, 3, 2, 3)
        assert cradle["w_class"] == "Hyper"


def _run():
    results = []
    for cls in (TestRotationGroup, TestTernaryMating, TestPieceTable, TestSignaturePieces):
        inst = cls()
        for name in sorted(dir(inst)):
            if name.startswith("test_"):
                try:
                    getattr(inst, name)()
                    results.append((f"{cls.__name__}.{name}", "ok"))
                except Exception as e:
                    results.append((f"{cls.__name__}.{name}", f"FAIL: {e}"))
    failed = [r for r in results if r[1] != "ok"]
    for name, status in results:
        print(f"  {status:4} {name}" if status == "ok" else f"  FAIL {name}: {status[6:]}")
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    _run()
