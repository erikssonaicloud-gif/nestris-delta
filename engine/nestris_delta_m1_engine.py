"""
NESTRIS Δ — M1 Engine: Precomputed Piece Table
==============================================
Stable canonical IDs on the **full 35-solid** space (0–34).

- 30 pure tetromino solids → playable (`pure_ids` / `playable_ids`)
- 5 monomino-derived solids → catalyst tier (`catalyst_ids`) — NOT game legendaries
- Game legendaries (spec §3.6): MONOLITH-Δ, REACTOR-Δ, HYPERCRADLE, PLATE-Δ

IMPORTANT: Never renumber by enumerating pure-only. Pure-only sort shifts every
ID (e.g. REACTOR pure=13 vs full=18). Always assign IDs from the full census.

Usage:
    from nestris_delta_m1_engine import PieceTable, PIECE_TABLE

    cells = PIECE_TABLE.get_cells(30, 0)          # HYPERCRADLE, rotation 0..191
    thin = PIECE_TABLE.thin_ids
    rid = PIECE_TABLE.named_legendaries["REACTOR-Δ"]
"""
from __future__ import annotations

import json
import os
from collections import defaultdict
from itertools import permutations, product
from pathlib import Path
from typing import Any

# ============================================================================
# ROTATION GROUP
# ============================================================================


def _get_permutation_sign(p):
    p = list(p)
    inv = sum(1 for i in range(len(p)) for j in range(i + 1, len(p)) if p[i] > p[j])
    return 1 if inv % 2 == 0 else -1


def precompute_rotations():
    proper = []
    for perm in permutations(range(4)):
        p_sign = _get_permutation_sign(perm)
        for signs in product([-1, 1], repeat=4):
            s_sign = 1
            for s in signs:
                s_sign *= s
            if p_sign * s_sign == 1:
                proper.append((perm, signs))
    return proper


ROTATIONS_192 = precompute_rotations()
assert len(ROTATIONS_192) == 192, f"Rotation group defect: {len(ROTATIONS_192)}"

# ============================================================================
# TERNARY MATING PRODUCT
# ============================================================================


class TernaryMatingProduct:
    PRIMARIES = {
        "I": [(0, 0), (1, 0), (2, 0), (3, 0)],
        "O": [(0, 0), (1, 0), (0, 1), (1, 1)],
        "T": [(0, 0), (1, 0), (2, 0), (1, 1)],
        "L": [(0, 0), (0, 1), (0, 2), (1, 2)],
        "Z": [(0, 0), (1, 0), (1, 1), (2, 1)],
        ".": [(0, 0)],
    }

    @staticmethod
    def _by_shared(shape):
        d = defaultdict(list)
        for free, shared in shape:
            d[shared].append(free)
        return d

    @staticmethod
    def mate3(a_key, b_key, c_key):
        a = TernaryMatingProduct._by_shared(TernaryMatingProduct.PRIMARIES[a_key])
        b = TernaryMatingProduct._by_shared(TernaryMatingProduct.PRIMARIES[b_key])
        c = TernaryMatingProduct._by_shared(TernaryMatingProduct.PRIMARIES[c_key])
        common_z = set(a.keys()) & set(b.keys()) & set(c.keys())
        cells = set()
        for z in common_z:
            for x in a[z]:
                for y in b[z]:
                    for w in c[z]:
                        cells.add((x, y, z, w))
        return sorted(cells)


def transform_cells(cells, rotation_index):
    perm, signs = ROTATIONS_192[rotation_index]
    rotated = [tuple(c[perm[i]] * signs[i] for i in range(4)) for c in cells]
    if not rotated:
        return []
    mins = [min(c[i] for c in rotated) for i in range(4)]
    return sorted([tuple(c[i] - mins[i] for i in range(4)) for c in rotated])


def canonical_form(cells):
    if not cells:
        return tuple()
    best = None
    for ri in range(192):
        rot = tuple(transform_cells(cells, ri))
        if best is None or rot < best:
            best = rot
    return best


def bbox(cells):
    if not cells:
        return (0, 0, 0, 0)
    return tuple(max(c[i] for c in cells) - min(c[i] for c in cells) + 1 for i in range(4))


def run_census(primaries):
    census = {}
    for a in primaries:
        for b in primaries:
            for c in primaries:
                cells = TernaryMatingProduct.mate3(a, b, c)
                if not cells:
                    continue
                cf = canonical_form(cells)
                name = f"({a},{b},{c})"
                if cf not in census:
                    census[cf] = {
                        "names": [name],
                        "volume": len(cells),
                        "dims": bbox(cells),
                        "cells": cf,
                    }
                else:
                    census[cf]["names"].append(name)
    return census


def _w_class(w_extent: int) -> str:
    if w_extent <= 1:
        return "Thin"
    if w_extent == 2:
        return "True"
    return "Hyper"


def _unique_orientations(cf):
    """unique_forms + rotation_to_form[192] mapping full group index → form index."""
    form_index = {}
    unique_forms = []
    rotation_to_form = []
    for ri in range(192):
        rot = tuple(transform_cells(list(cf), ri))
        if rot not in form_index:
            form_index[rot] = len(unique_forms)
            unique_forms.append([list(c) for c in rot])
        rotation_to_form.append(form_index[rot])
    return unique_forms, rotation_to_form


# Game legendaries (spec §3.6) — resolved after census by generator / orbit.
NAMED_LEGENDARY_GENERATORS = {
    "REACTOR-Δ": ("O", "O", "O"),
    "PLATE-Δ": ("I", "I", "I"),
    "HYPERCRADLE": ("T", "T", "T"),
}

DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_JSON_35 = DATA_DIR / "piece_table_35.json"
DEFAULT_JSON_30 = DATA_DIR / "piece_table_30.json"  # pure-only export (IDs remapped — prefer 35)
DEFAULT_COMPACT = DATA_DIR / "piece_table_v1.json"

# ============================================================================
# PIECE TABLE
# ============================================================================


class PieceTable:
    """
    Static lookup for canonical solids on the full 35-ID space.

    get_cells(id, rotation_idx) — rotation_idx is 0..191 (group index).
    """

    PURE_PRIMARIES = ["I", "O", "T", "L", "Z"]
    FULL_PRIMARIES = ["I", "O", "T", "L", "Z", "."]

    def __init__(self, build: bool = True):
        if not build:
            return
        self._build_from_census()

    def _build_from_census(self):
        # Reset primaries (tests may mutate)
        TernaryMatingProduct.PRIMARIES.clear()
        TernaryMatingProduct.PRIMARIES.update(
            {
                "I": [(0, 0), (1, 0), (2, 0), (3, 0)],
                "O": [(0, 0), (1, 0), (0, 1), (1, 1)],
                "T": [(0, 0), (1, 0), (2, 0), (1, 1)],
                "L": [(0, 0), (0, 1), (0, 2), (1, 2)],
                "Z": [(0, 0), (1, 0), (1, 1), (2, 1)],
                ".": [(0, 0)],
            }
        )

        pure_forms = set(run_census(self.PURE_PRIMARIES).keys())
        full_census = run_census(self.FULL_PRIMARIES)

        ordered = sorted(
            full_census.items(),
            key=lambda x: (x[1]["volume"], x[1]["dims"], x[0]),
        )

        self.solids = []
        self.by_id = {}

        for idx, (cf, meta) in enumerate(ordered):
            unique_forms, rotation_to_form = _unique_orientations(cf)
            names = sorted(meta["names"])
            dims = meta["dims"]
            w_extent = dims[3]
            solid = {
                "id": idx,
                "canonical_name": names[0],
                "all_names": names,
                "volume": meta["volume"],
                "dims": dims,
                "w_extent": w_extent,
                "w_class": _w_class(w_extent),
                "is_pure": cf in pure_forms,
                "canonical_cells": [list(c) for c in cf],
                "unique_forms": unique_forms,
                "rotation_to_form": rotation_to_form,
                "symmetry_count": len(unique_forms),
                # verbose alias: unique orbit representatives (not full 192)
                "rotations": [[tuple(c) for c in form] for form in unique_forms],
                "named_legendary": None,
            }
            self.solids.append(solid)
            self.by_id[idx] = solid

        self._tag_named_legendaries()
        self._recompute_buckets()

    def _tag_named_legendaries(self):
        self.named_legendaries: dict[str, int] = {}

        for name, gen in NAMED_LEGENDARY_GENERATORS.items():
            cells = TernaryMatingProduct.mate3(*gen)
            cf = canonical_form(cells)
            for s in self.solids:
                if tuple(map(tuple, s["canonical_cells"])) == cf:
                    s["named_legendary"] = name
                    self.named_legendaries[name] = s["id"]
                    break
            else:
                raise RuntimeError(f"Legendary {name} missing from census")

        # MONOLITH-Δ = 4-cell axis bar (same orbit as vertical I×I×I)
        TernaryMatingProduct.PRIMARIES["Iv"] = [(0, z) for z in range(4)]
        mono_cf = canonical_form(TernaryMatingProduct.mate3("Iv", "Iv", "Iv"))
        del TernaryMatingProduct.PRIMARIES["Iv"]
        for s in self.solids:
            if tuple(map(tuple, s["canonical_cells"])) == mono_cf:
                if s["named_legendary"] is None:
                    s["named_legendary"] = "MONOLITH-Δ"
                self.named_legendaries["MONOLITH-Δ"] = s["id"]
                break
        else:
            raise RuntimeError("MONOLITH-Δ orbit missing from census")

    def _recompute_buckets(self):
        self.thin_ids = [s["id"] for s in self.solids if s["w_extent"] == 1]
        self.true_ids = [s["id"] for s in self.solids if s["w_extent"] == 2]
        self.hyper_ids = [s["id"] for s in self.solids if s["w_extent"] >= 3]
        self.pure_ids = [s["id"] for s in self.solids if s["is_pure"]]
        self.playable_ids = list(self.pure_ids)
        # Monomino-derived catalyst tier (NOT spec legendaries)
        self.catalyst_ids = [s["id"] for s in self.solids if not s["is_pure"]]
        # Back-compat alias used by Downloads tests (misnamed "legendary")
        self.legendary_ids = list(self.catalyst_ids)

    # ----- lookup -----

    def get_cells(self, solid_id: int, rotation_idx: int = 0):
        """Cells for solid at full-group rotation index 0..191."""
        s = self.by_id[solid_id]
        if not (0 <= rotation_idx < 192):
            raise IndexError(f"rotation_idx {rotation_idx} out of range 0..191")
        form_i = s["rotation_to_form"][rotation_idx]
        return [tuple(c) for c in s["unique_forms"][form_i]]

    def get_cells_unique(self, solid_id: int, unique_idx: int = 0):
        """Cells by unique-orbit index (0 .. symmetry_count-1)."""
        s = self.by_id[solid_id]
        rots = s["rotations"]
        return list(rots[unique_idx % len(rots)])

    def get_bbox(self, solid_id: int, rotation_idx: int = 0):
        return bbox(self.get_cells(solid_id, rotation_idx))

    def get_volume(self, solid_id: int) -> int:
        return self.by_id[solid_id]["volume"]

    def get_w_extent(self, solid_id: int) -> int:
        return self.by_id[solid_id]["w_extent"]

    def get_symmetry_count(self, solid_id: int) -> int:
        return self.by_id[solid_id]["symmetry_count"]

    def legendary_id(self, name: str) -> int:
        if name not in self.named_legendaries:
            raise KeyError(f"Unknown named legendary: {name}")
        return self.named_legendaries[name]

    # ----- serialization -----

    def to_json(self, pure_only: bool = False) -> list[dict[str, Any]]:
        """
        Verbose export. IDs always from the full 35-space.
        pure_only=True filters to pure solids but **keeps full-space IDs**.
        """
        out = []
        for s in self.solids:
            if pure_only and not s["is_pure"]:
                continue
            out.append(
                {
                    "id": s["id"],
                    "canonical_name": s["canonical_name"],
                    "all_names": s["all_names"],
                    "volume": s["volume"],
                    "dims": list(s["dims"]),
                    "w_extent": s["w_extent"],
                    "w_class": s["w_class"],
                    "is_pure": s["is_pure"],
                    "named_legendary": s["named_legendary"],
                    "symmetry_count": s["symmetry_count"],
                    "canonical_cells": s["canonical_cells"],
                    "unique_forms": s["unique_forms"],
                    "rotation_to_form": s["rotation_to_form"],
                    # orbit reps (same as unique_forms as tuples-of-lists)
                    "rotations": s["unique_forms"],
                }
            )
        return out

    def to_compact_json(self) -> dict[str, Any]:
        """Compact format compatible with piece_table_v1.json consumers."""
        pieces = []
        for s in self.solids:
            pieces.append(
                {
                    "id": s["id"],
                    "volume": s["volume"],
                    "dims": list(s["dims"]),
                    "phase_class": s["w_class"].lower(),
                    "playable": s["is_pure"],
                    "legendary": s["named_legendary"],
                    "generators": s["all_names"],
                    "canonical": s["canonical_cells"],
                    "unique_forms": s["unique_forms"],
                    "rotation_to_form": s["rotation_to_form"],
                    "n_unique_orientations": s["symmetry_count"],
                }
            )
        phase_bags = {
            "thin": [i for i in self.thin_ids if i in self.playable_ids],
            "true": [i for i in self.true_ids if i in self.playable_ids],
            "hyper": [i for i in self.hyper_ids if i in self.playable_ids],
        }
        return {
            "version": 1,
            "rotation_count": 192,
            "piece_count": len(self.solids),
            "playable_count": len(self.playable_ids),
            "playable_ids": self.playable_ids,
            "catalyst_ids": self.catalyst_ids,
            "phase_bags": phase_bags,
            "legendaries": dict(self.named_legendaries),
            "pieces": pieces,
        }

    def save_json(self, path, pure_only: bool = False):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_json(pure_only=pure_only), f, indent=2)

    def save_compact(self, path=None):
        path = Path(path or DEFAULT_COMPACT)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_compact_json(), f, separators=(",", ":"))
        summary = {
            "version": 1,
            "piece_count": len(self.solids),
            "playable_count": len(self.playable_ids),
            "playable_ids": self.playable_ids,
            "catalyst_ids": self.catalyst_ids,
            "phase_bags": {
                "thin": [i for i in self.thin_ids if i in self.playable_ids],
                "true": [i for i in self.true_ids if i in self.playable_ids],
                "hyper": [i for i in self.hyper_ids if i in self.playable_ids],
            },
            "legendaries": dict(self.named_legendaries),
            "pieces": [
                {
                    "id": s["id"],
                    "volume": s["volume"],
                    "dims": list(s["dims"]),
                    "w_class": s["w_class"],
                    "is_pure": s["is_pure"],
                    "named_legendary": s["named_legendary"],
                    "symmetry_count": s["symmetry_count"],
                    "canonical_name": s["canonical_name"],
                }
                for s in self.solids
            ],
        }
        summary_path = path.with_name(path.stem + "_summary.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        return path

    @classmethod
    def from_json(cls, path):
        """Load precomputed table from verbose or compact JSON."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        pt = cls(build=False)
        pt.solids = []
        pt.by_id = {}
        pt.named_legendaries = {}

        # Compact format
        if isinstance(data, dict) and "pieces" in data:
            for entry in data["pieces"]:
                unique_forms = entry["unique_forms"]
                rotation_to_form = entry["rotation_to_form"]
                solid = {
                    "id": entry["id"],
                    "canonical_name": (entry.get("generators") or ["?"])[0],
                    "all_names": entry.get("generators") or [],
                    "volume": entry["volume"],
                    "dims": tuple(entry["dims"]),
                    "w_extent": entry["dims"][3],
                    "w_class": entry.get("phase_class", _w_class(entry["dims"][3])).title()
                    if entry.get("phase_class")
                    else _w_class(entry["dims"][3]),
                    "is_pure": entry.get("playable", True),
                    "canonical_cells": entry["canonical"],
                    "unique_forms": unique_forms,
                    "rotation_to_form": rotation_to_form,
                    "symmetry_count": entry.get("n_unique_orientations", len(unique_forms)),
                    "rotations": [[tuple(c) for c in form] for form in unique_forms],
                    "named_legendary": entry.get("legendary"),
                }
                # normalize w_class
                we = solid["w_extent"]
                solid["w_class"] = _w_class(we)
                pt.solids.append(solid)
                pt.by_id[solid["id"]] = solid
                if solid["named_legendary"]:
                    pt.named_legendaries[solid["named_legendary"]] = solid["id"]
            if data.get("legendaries"):
                pt.named_legendaries.update(data["legendaries"])
            pt._recompute_buckets()
            return pt

        # Verbose list format
        if not isinstance(data, list):
            raise ValueError(f"Unrecognized piece table JSON shape in {path}")

        for entry in data:
            unique_forms = entry.get("unique_forms") or entry.get("rotations")
            rotation_to_form = entry.get("rotation_to_form")
            if rotation_to_form is None:
                # Rebuild 192 map from unique forms by re-transforming if needed
                # Fallback: identity map onto unique forms only (len may be < 192)
                rotation_to_form = list(range(len(unique_forms)))
                # pad/repeat is wrong for 192; recompute from canonical
                cf = [tuple(c) for c in entry["canonical_cells"]]
                unique_forms, rotation_to_form = _unique_orientations(cf)

            solid = {
                "id": entry["id"],
                "canonical_name": entry["canonical_name"],
                "all_names": entry["all_names"],
                "volume": entry["volume"],
                "dims": tuple(entry["dims"]),
                "w_extent": entry["w_extent"],
                "w_class": entry["w_class"],
                "is_pure": entry["is_pure"],
                "canonical_cells": entry["canonical_cells"],
                "unique_forms": unique_forms,
                "rotation_to_form": rotation_to_form,
                "symmetry_count": entry.get("symmetry_count", len(unique_forms)),
                "rotations": [[tuple(c) for c in form] for form in unique_forms],
                "named_legendary": entry.get("named_legendary"),
            }
            pt.solids.append(solid)
            pt.by_id[solid["id"]] = solid
            if solid["named_legendary"]:
                pt.named_legendaries[solid["named_legendary"]] = solid["id"]

        # Ensure named legendaries resolved if missing from file
        if len(pt.named_legendaries) < 3:
            pt._tag_named_legendaries()
        pt._recompute_buckets()
        return pt


# ============================================================================
# GLOBAL INSTANCE — full 35-space only (stable IDs)
# ============================================================================

PIECE_TABLE = PieceTable()  # full 35; use .pure_ids / .playable_ids for bags
PIECE_TABLE_FULL = PIECE_TABLE  # alias — no second renumbered table


def rebuild_and_export():
    """Rebuild tables and write engine/data artifacts."""
    pt = PieceTable()
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Verbose 35 (stable IDs)
    pt.save_json(DEFAULT_JSON_35, pure_only=False)
    # Verbose 30 pure subset — **same full-space IDs**, filtered
    pt.save_json(DEFAULT_JSON_30, pure_only=True)
    compact = pt.save_compact(DEFAULT_COMPACT)

    print("NESTRIS Δ — M1 Piece Table (stable full-space IDs)")
    print("=" * 50)
    print(f"  solids:     {len(pt.solids)}")
    print(f"  playable:   {len(pt.playable_ids)} → {pt.playable_ids}")
    print(f"  catalyst:   {pt.catalyst_ids}")
    print(f"  thin/true/hyper (playable): "
          f"{len([i for i in pt.thin_ids if i in pt.playable_ids])}/"
          f"{len([i for i in pt.true_ids if i in pt.playable_ids])}/"
          f"{len([i for i in pt.hyper_ids if i in pt.playable_ids])}")
    print(f"  named:      {pt.named_legendaries}")
    for name, expected_v in [("REACTOR-Δ", 16), ("HYPERCRADLE", 28), ("PLATE-Δ", 64), ("MONOLITH-Δ", 4)]:
        sid = pt.named_legendaries[name]
        s = pt.by_id[sid]
        assert s["volume"] == expected_v, (name, s["volume"], expected_v)
        print(f"  {name}: id={sid} V={s['volume']} dims={s['dims']} sym={s['symmetry_count']} ✓")
    print(f"\n  wrote {DEFAULT_JSON_35}")
    print(f"  wrote {DEFAULT_JSON_30}  (pure subset, full-space IDs)")
    print(f"  wrote {compact}")
    return pt


if __name__ == "__main__":
    rebuild_and_export()
