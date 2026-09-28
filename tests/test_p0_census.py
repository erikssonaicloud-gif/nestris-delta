"""P0 sanity: rotation group, legendaries, census size, S/J collapse."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))

from nestris_delta_p0_v02 import (
    ROTATIONS_192,
    TernaryMatingProduct as TMP,
    run_census,
    canonical_form,
    bbox,
    transform_cells,
)

BASE_PRIMARIES = {
    "I": [(0, 0), (1, 0), (2, 0), (3, 0)],
    "O": [(0, 0), (1, 0), (0, 1), (1, 1)],
    "T": [(0, 0), (1, 0), (2, 0), (1, 1)],
    "L": [(0, 0), (0, 1), (0, 2), (1, 2)],
    "Z": [(0, 0), (1, 0), (1, 1), (2, 1)],
    ".": [(0, 0)],
}


def _restore_primaries(extra=None):
    TMP.PRIMARIES.clear()
    TMP.PRIMARIES.update(BASE_PRIMARIES)
    if extra:
        TMP.PRIMARIES.update(extra)


def test_rotation_group_order():
    assert len(ROTATIONS_192) == 192


def test_legendaries():
    _restore_primaries()
    assert len(TMP.mate3("T", "T", "T")) == 28
    assert len(TMP.mate3("O", "O", "O")) == 16
    assert bbox(TMP.mate3("O", "O", "O")) == (2, 2, 2, 2)
    assert len(TMP.mate3("I", "I", "I")) == 64


def test_monolith_vertical_i():
    _restore_primaries({"Iv": [(0, z) for z in range(4)]})
    mono = TMP.mate3("Iv", "Iv", "Iv")
    assert len(mono) == 4
    assert bbox(mono) == (1, 1, 4, 1)
    _restore_primaries()


def test_census_35():
    _restore_primaries()
    census = run_census()
    assert len(census) == 35, f"got {len(census)}"


def test_rotation_preserves_cardinality():
    _restore_primaries()
    cells = TMP.mate3("T", "T", "T")
    rot = transform_cells(cells, 42)
    assert len(set(rot)) == len(cells)


def test_sj_collapse():
    _restore_primaries(
        {
            "S": [(1, 0), (2, 0), (0, 1), (1, 1)],
            "J": [(1, 0), (1, 1), (1, 2), (0, 2)],
        }
    )

    def census_of(keys):
        c = set()
        for a in keys:
            for b in keys:
                for ck in keys:
                    cells = TMP.mate3(a, b, ck)
                    if cells:
                        c.add(canonical_form(cells))
        return c

    c5 = census_of(["I", "O", "T", "L", "Z"])
    c7 = census_of(["I", "O", "T", "L", "Z", "S", "J"])
    assert len(c5) == 30
    assert len(c7) == 30
    assert c7 == c5
    _restore_primaries()


if __name__ == "__main__":
    test_rotation_group_order()
    test_legendaries()
    test_monolith_vertical_i()
    test_census_35()
    test_rotation_preserves_cardinality()
    test_sj_collapse()
    print("All P0 tests passed.")
