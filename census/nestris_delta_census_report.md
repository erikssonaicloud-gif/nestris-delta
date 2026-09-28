# NESTRIS Δ — §3.4 Canonical Solid Census

**Source:** `engine/nestris_delta_p0_v02.py`  
**Run date:** 2026-07-19  
**Spec:** `docs/NESTRIS_DELTA_Spec_v0.1.md` §3.4  

---

## Verdict

| Claim | Status |
|-------|--------|
| Ternary product `𝟙_M = 𝟙_A·𝟙_B·𝟙_C` | ✓ Verified |
| 192-rotation group (det = +1) | ✓ Verified (order 192) |
| REACTOR-Δ V=16, tesseract `(2,2,2,2)` | ✓ `(O,O,O)` |
| PLATE-Δ V=64, dims `(4,4,1,4)` | ✓ `(I,I,I)` |
| HYPERCRADLE V=28, 27-cell plate + 1 stem | ✓ `(T,T,T)` |
| Overhang shell 26 | ✓ (plate − stem projection) |
| MONOLITH-Δ V=4 | ✓ vertical I only (`Iv,Iv,Iv`) — needs orientation enum |
| J/S chirality in 4D | **Collapsed** — 0 new solids over `{I,O,T,L,Z}` |
| HYPERHELIX `(S,Z,T)` | V=16 — exists; chirality not yet proven unique under rotation |

**Canonical set (this reference implementation):**

| Primary set | Unique solids |
|-------------|---------------|
| `{I,O,T,L,Z,.}` (6, includes monomino) | **35** |
| `{I,O,T,L,Z}` (5 pure tetromino) | **30** |
| `{I,O,T,L,Z,S,J}` (7 classic) | **30** (S/J add nothing) |

The v0.1 estimate of “400–900” assumed weaker collapse under the 192-group and full orientation×δ enumeration. **Under fixed base orientations with no δ offsets, the set is tiny.** That is good news for engine architecture: full pre-rotation tables are cheap.

---

## Scope of this census (honest bounds)

This P0 census enumerates:

```
for a,b,c in primaries³:
    M = mate3(a,b,c)   # shared-z row product only
    fold under 192 proper rotations → canonical form
```

**Not yet enumerated (spec §3.3–§3.4 full):**

1. Planar orientations of each parent (up to 4 each)
2. Vertical alignment offsets `δ_B`, `δ_C`
3. Connectivity filter (8-connectivity reject)
4. Boundedness filter (bbox ≤ 4×4×4×4 — most pass; PLATE is on the edge)
5. Spawnability filter

So **35 / 30 is the fixed-orientation floor**, not necessarily the final game set. Expanding orientations + δ will grow the table; S/J still likely collapse. **Recommendation:** lock the fixed-orientation 30-tetromino + 4 legendaries path for M1–M4 (ship), then re-run full orientation×δ census as M0b research if design needs more shape variety.

---

## Volume histogram (35-solid set)

| V | Count | Notes |
|---|-------|-------|
| 1 | 1 | monomino product `(.,.,.)` |
| 2 | 1 | |
| 3 | 1 | |
| 4 | 4 | includes thin bars / catalysts |
| 6 | 1 | |
| 8 | 6 | |
| 9 | 1 | |
| 10 | 2 | includes `(L,L,L)` |
| 12 | 1 | |
| 16 | 9 | includes REACTOR `(O,O,O)` |
| 20 | 2 | |
| 24 | 1 | |
| 28 | 1 | **HYPERCRADLE** |
| 32 | 1 | |
| 36 | 1 | |
| 48 | 1 | |
| 64 | 1 | **PLATE** |

Generator triples folded into the 35: **216** (6³ with empty products dropped).

---

## Named legendaries

| Name | Tuple | V | Dims (axis-aligned) | In 35-set? |
|------|-------|---|---------------------|------------|
| **REACTOR-Δ** | O⊗O⊗O | 16 | (2,2,2,2) | ✓ |
| **PLATE-Δ** | I⊗I⊗I (horiz) | 64 | (4,4,1,4) | ✓ |
| **HYPERCRADLE** | T⊗T⊗T | 28 | (3,3,2,3) | ✓ |
| **MONOLITH-Δ** | I_vert⊗I_vert⊗I_vert | 4 | (1,1,4,1) | needs vertical I primary |
| **HYPERHELIX\*** | S⊗Z⊗T | 16 | (3,3,2,3) | candidate; same volume band as several others |

### HYPERCRADLE geometry check

T primary (fixed base form): free bar `{0,1,2}` at shared z=0, stem `{1}` at z=1.

| z | r_A · r_B · r_C | Cells |
|---|-----------------|-------|
| 0 | 3×3×3 | 27 |
| 1 | 1×1×1 | 1 |
| **Σ** | | **28** |

Overhang shell under the plate = 27 − 1 = **26** empty hyper-cells (spec §3.5).

### S/J collapse

| Set | Solids |
|-----|--------|
| `{I,O,T,L,Z}` | 30 |
| `{I,O,T,L,Z,S,J}` | 30 |
| New from S/J | **0** |

The 4D rotation group maps S↔Z and L↔J images into the same chiral orbits for these products. Spec language that “S and Z remain distinct” still holds at the *parent* level for generation UI, but they do not expand the *canonical solid* table under 192-fold.

---

## Full solid table (35)

See `census/census_raw.json` for generator lists. Index ordered by volume, then dims:

| ID | V | Dims | #gens | Example |
|----|---|------|-------|---------|
| 00 | 1 | (1,1,1,1) | 7 | `(.,.,.)` |
| 01 | 2 | (2,1,1,1) | 18 | `(.,.,O)` |
| 02 | 3 | (3,1,1,1) | 9 | `(.,.,T)` |
| 03 | 4 | (1,1,2,3) | 3 | `(L,L,Z)` |
| 04 | 4 | (2,2,1,1) | 15 | `(.,O,O)` |
| 05 | 4 | (3,1,2,1) | 3 | `(L,L,T)` |
| 06 | 4 | (4,1,1,1) | 12 | `(.,.,I)` |
| 07 | 6 | (2,3,1,1) | 12 | `(.,O,T)` |
| 08 | 8 | (1,3,2,3) | 3 | `(L,Z,Z)` |
| 09 | 8 | (2,1,2,3) | 6 | `(L,O,Z)` |
| 10 | 8 | (2,2,2,1) | 3 | `(L,O,O)` |
| 11 | 8 | (2,3,2,1) | 6 | `(L,O,T)` |
| 12 | 8 | (3,1,2,3) | 6 | `(L,T,Z)` |
| 13 | 8 | (4,2,1,1) | 24 | `(.,I,O)` |
| 14 | 9 | (3,3,1,1) | 3 | `(.,T,T)` |
| 15 | 10 | (2,2,3,2) | 1 | `(L,L,L)` |
| 16 | 10 | (3,3,2,1) | 3 | `(L,T,T)` |
| 17 | 12 | (4,3,1,1) | 12 | `(.,I,T)` |
| 18 | 16 | (2,2,2,2) | 1 | `(O,O,O)` **REACTOR** |
| 19–26 | 16 | various | … | O/T/Z mixes, `(.,I,I)` |
| 27–28 | 20 | … | … | |
| 29 | 24 | (4,2,1,3) | 12 | `(I,O,T)` |
| 30 | 28 | (3,3,2,3) | 1 | `(T,T,T)` **HYPERCRADLE** |
| 31 | 32 | (4,4,1,2) | 6 | `(I,I,O)` |
| 32 | 36 | (4,3,1,3) | 3 | `(I,T,T)` |
| 33 | 48 | (4,4,1,3) | 3 | `(I,I,T)` |
| 34 | 64 | (4,4,1,4) | 1 | `(I,I,I)` **PLATE** |

---

## Reproduce

```bash
cd ~/nestris-delta
python3 engine/nestris_delta_p0_v02.py
# → Canonical solids: 35 + legendary asserts
```

Machine-readable dump: `census/census_raw.json`.
