# NESTRIS Δ — v0.2 Implementation Blueprint

**Status:** M0 + **M1 complete** (piece table frozen)  
**Lineage:** Successor to NESTRIS 3D v0.2 (`docs/lineage_*`)  
**Authoritative design draft:** `docs/NESTRIS_DELTA_Spec_v0.1.md`  
**Reference code:** `engine/nestris_delta_p0_v02.py`, `engine/piece_table.py`  
**Census:** `census/nestris_delta_census_report.md`  
**Frozen table:** `engine/data/piece_table_v1.json`

---

## 0. Design pivot from census

The v0.1 draft estimated **400–900** canonical solids. The fixed-orientation census produced:

- **35** solids with monomino catalyst `{I,O,T,L,Z,.}`
- **30** solids with pure tetrominoes `{I,O,T,L,Z}`
- **+S,+J → 0 new solids** (4D rotation collapse)

**Ship decision (recommended):** Lock the **30 tetromino + monomino-optional + hand legendaries** canon for the playable prototype. Full orientation×δ re-census is optional research (M0b), not a blocker.

Consequences:

1. Piece table is tiny → full 30×192 precompute is trivial (~tens of KB).
2. Randomizer does not need deep tiering to tame combinatorics; tier by **volume** and **w-extent class** instead.
3. Human-learnable taxonomy is realistic.

---

## 1. Piece table architecture (precomputed)

```
PIECE_TABLE[canonical_id][rotation_idx] → sorted tuple of (x,y,z,w) cells
```

At runtime a piece instance carries:

| Field | Range | Notes |
|-------|-------|-------|
| `canonical_id` | 0–29 (or 0–34) | index into census |
| `rotation_idx` | 0–191 | into `ROTATIONS_192` |
| `size_class` | {½, 1, 2} | scales cell lattice |
| `position` | (x,y,z,w) | anchor in subcells |
| `phase_view` | 0–7 | which brane the player is looking at (UI) |

**Memory budget (order-of-magnitude):**  
35 × 192 × ~20 avg cells × 4 ints ≈ **~1M ints** worst case if naively stored; store sparse cell lists per (id, rot) only for distinct orbits after symmetry collapse (REACTOR has 1 orientation).

Load-time: run `mate3` + `canonical_form` once, assign stable IDs, freeze JSON/binary table.

---

## 2. Triple-bag randomizer

Bucket solids by **maximum free-axis extent in canonical form** (proxy for phase pressure). Recompute buckets from census dims after sorting axes:

| Class | Typical max extent | Role |
|-------|-------------------|------|
| **Thin** | extent 1 on ≥1 axis | Seam fillers, brane-local |
| **True** | extent 2 | Default play (REACTOR, many O/T mixes) |
| **Hyper** | extent ≥3 | Forces multi-brane reasoning (PLATE, HYPERCRADLE, long I products) |

Three independent bags (replenish when empty):

1. **Shape bag** — uniform over playable solid IDs (exclude pure monomino toys unless debug)
2. **Size bag** — baseline weights: Half 25% / Normal 55% / Double 20% (from Δ v0.1 §4)
3. **Phase-class bag** — Thin / True / Hyper mix (tune in playtest; start 40/40/20)

**Legendary injection:** every bag of 12 draws includes **exactly 1** of  
`{MONOLITH-Δ, REACTOR-Δ, HYPERCRADLE, PLATE-Δ}` (HYPERHELIX pending chirality proof).

---

## 3. HyperWell (already in P0)

Default: **16 × 16 × 32 × 8** subcells (W×D×H×P) + 4 hidden spawn slabs in z.

```
data[w][z][y] → W-bit row mask
```

API (P0):

- `check_collision(cells, offset) → bool`
- `lock_piece(cells, offset)`
- `clear_full_hyper_slabs() → n_cleared`  # full x·y·w at fixed z

**M2 upgrades:**

- Pack to uint64 slab-words per Δ §7 if profiling needs it
- Spawn buffer fail if any locked voxel has `z ≥ H`

---

## 4. Phase Slide (post-lock)

**Atomic rule:** after lock, during grace window, the piece may translate by **±1 in w only** (all cells together) if the destination is collision-free.

Optional skill filter (stricter, hyperpocket-aware):

```python
def phase_slide_legal(cells, well, dw):
    moved = [(x, y, z, w + dw) for x, y, z, w in cells]
    if well.check_collision(moved, (0, 0, 0, 0)):
        return False
    # optional: require at least one cell enter a shielded pocket
    return True
```

**Channel axis (full Δ §9):** generalize later to prismatic slides on x/y/z/w; Phase Slide is the w-special case that protects the hyperdensity economy.

**Hyperpocket (Δ §10):** empty cell shielded on ≥5 of 8 axis directions (±x±y±z±w). HYPERCRADLE-class hosts create these under the 26-cell overhang shell.

---

## 5. Hyperdensity & death

| Metric | Formula | Threshold (start) |
|--------|---------|-------------------|
| Local density | filled / (W·D·H) **per brane** | > 0.85 → warning |
| Hyperdensity | filled / (W·D·H·P) **global** | > 0.40 → death |

**Shadow-stacking penalty:** if local > 0.85 and hyperdensity < 0.20, force next 3 shape/phase draws toward **Hyper** class (push cross-brane play).

Tune in M8; numbers are design starts, not sacred.

---

## 6. Clears, cascade, nesting score

On full hyper-slab clear at z:

1. Drop all cells with higher z by 1 (vertical cascade).
2. **Nest check:** cells sharing (x,y,z) across distinct w form nest pairs; score ×2^pairs (cap / full-8-brane nest = ×64 + hyperdensity relief).
3. Re-test clears (cascade chains).

*Note:* Δ v0.1 leaves cascade open for v0.2; implement simple gravity cascade first, nesting multipliers second.

---

## 7. Orientation & kicks

- Runtime rotation = table lookup on `rotation_idx`, never continuous SO(4).
- Six plane generators: xy, xz, yz, xw, yw, zw → precomputed index permutations on 0..191.
- Kick table: Δ v0.1 §5.2 (even subcell offsets; scale with size class).

---

## 8. Rendering constraint

**True 4D state, 3D operational interface.**

- One active brane `w = phase_view` rendered as a 3D NESTRIS-like well (reuse 3D prototype camera lessons from `docs/lineage_nestris3d_prototype.html`).
- Ghost: silhouette of active piece in adjacent branes.
- Phase indicator: which of 8 branes is live.

Do not build a second independent board. One solid, navigable w.

---

## 9. Milestone roadmap

| Milestone | Deliverable | Status |
|-----------|-------------|--------|
| **M0** | P0 code + 192 group + TMP + census | **Done** |
| **M0b** | Optional full orientation×δ census | Research |
| **M1** | Precomputed piece table (35 solids, 30 playable) + stable IDs | **Done** |
| **M2** | HyperWell bitboard + collision + lock | P0 stub exists |
| **M3** | Triple-bag randomizer + spawn | **Next** |
| **M4** | Phase Slide + hyperpocket detection | |
| **M5** | Hyper-slab clear + cascade | P0 clear exists |
| **M6** | Hyperdensity tracker + penalty | |
| **M7** | 3D brane renderer | High effort |
| **M8** | Playtest + threshold tuning | Ongoing |

**Fast path to playable:** M1→M3→M5→M7 minimal (gravity + lock + clear + brane view), then M4/M6 for the density fantasy.

---

## 10. Open question — resolved for ship

| Option | Decision |
|--------|----------|
| **1. Lock ~30–35 solid canon** | **Yes — build engine on this** |
| 2. Expand primaries (pentominoes) / full δ×orient | Defer to post-prototype research |

If M0b orientation×δ census stays under ~100 solids, absorb into the same table architecture without redesign.

---

## 11. File map

```
nestris-delta/
  engine/nestris_delta_p0_v02.py     # reference implementation
  census/nestris_delta_census_report.md
  census/census_raw.json
  blueprint/NESTRIS_DELTA_v0.2_Blueprint.md  # this file
  docs/NESTRIS_DELTA_Spec_v0.1.md
  docs/lineage_*                     # 3D ancestor specs + prototype
  tests/
  README.md
```

### Source copies (Downloads)

- `~/Downloads/nestris_delta_p0_v02.py`
- `~/Downloads/NESTRIS Δ — Transdimensional Technical Specification v0.1.md`
- `~/Downloads/NESTRIS_3D_Spec_v0.2.md`
- `~/Downloads/NESTRIS-3D-Technical-Spec.md`
- `~/Downloads/nestris3d_prototype_html.html`
