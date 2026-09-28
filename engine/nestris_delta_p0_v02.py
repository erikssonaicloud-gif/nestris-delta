"""
NESTRIS Δ — P0 Reference Implementation v0.2
Fixed Rotation Group & Ternary Mating Product (TMP) Piece Generation

Canonical census: 35 unique solids from 6 primaries under the 192-rotation group.
"""
from itertools import permutations, product
from collections import defaultdict, Counter

# ---------------------------------------------------------------------------
# 1. ROTATION GROUP (192 proper rotations of the 4-cube)
# ---------------------------------------------------------------------------

def _get_permutation_sign(p):
    """Parity of a permutation: +1 even, -1 odd."""
    p = list(p)
    inv = sum(1 for i in range(len(p)) for j in range(i+1, len(p)) if p[i] > p[j])
    return 1 if inv % 2 == 0 else -1

def precompute_rotations():
    """Generate the 192 orientation-preserving rotations of the tesseract."""
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
assert len(ROTATIONS_192) == 192

# ---------------------------------------------------------------------------
# 2. TERNARY MATING PRODUCT
# ---------------------------------------------------------------------------

class TernaryMatingProduct:
    """
    𝟙_M(x,y,z,w) = 𝟙_A(x,z) · 𝟙_B(y,z) · 𝟙_C(w,z)

    Three 2D primaries share the z-axis; their free axes map to x, y, w.
    For each common z-layer, the Cartesian product of free extents becomes
    a 4D cell set.
    """
    PRIMARIES = {
        'I': [(0,0), (1,0), (2,0), (3,0)],   # 4×1 bar
        'O': [(0,0), (1,0), (0,1), (1,1)],   # 2×2 square
        'T': [(0,0), (1,0), (2,0), (1,1)],   # T-tetromino
        'L': [(0,0), (0,1), (0,2), (1,2)],   # L-tetromino
        'Z': [(0,0), (1,0), (1,1), (2,1)],   # Z-tetromino
        '.': [(0,0)],                          # Monomino catalyst
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

# ---------------------------------------------------------------------------
# 3. CANONICAL SOLID UTILITIES
# ---------------------------------------------------------------------------

def transform_cells(cells, rotation_index):
    """Apply a proper rotation; normalize to positive orthant."""
    perm, signs = ROTATIONS_192[rotation_index]
    rotated = [tuple(c[perm[i]] * signs[i] for i in range(4)) for c in cells]
    if not rotated:
        return []
    mins = [min(c[i] for c in rotated) for i in range(4)]
    return sorted([tuple(c[i] - mins[i] for i in range(4)) for c in rotated])

def canonical_form(cells):
    """Lexicographically-minimum form under the 192-rotation group."""
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

# ---------------------------------------------------------------------------
# 4. CENSUS
# ---------------------------------------------------------------------------

def run_census():
    primaries = list(TernaryMatingProduct.PRIMARIES.keys())
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
                        'names': [name],
                        'volume': len(cells),
                        'dims': bbox(cells),
                        'cells': cf,
                    }
                else:
                    census[cf]['names'].append(name)
    return census

# ---------------------------------------------------------------------------
# 5. HYPERWELL (4D playfield)
# ---------------------------------------------------------------------------

class HyperWell:
    """
    4D play volume: W×D×H×P subcells (default 16×16×32×8).
    Bit-packed per brane for collision and clearing.
    """
    def __init__(self, width=16, depth=16, height=32, phases=8):
        self.W, self.D, self.H, self.P = width, depth, height, phases
        # branes[w][z][y] -> W-bit integer mask
        self.data = [[[0 for _ in range(self.D)] 
                       for _ in range(self.H + 4)] 
                      for _ in range(self.P)]

    def check_collision(self, piece_cells, offset):
        ox, oy, oz, ow = offset
        for px, py, pz, pw in piece_cells:
            tx, ty, tz, tw = px + ox, py + oy, pz + oz, pw + ow
            if not (0 <= tx < self.W and 0 <= ty < self.D 
                    and 0 <= tz < (self.H + 4) and 0 <= tw < self.P):
                return True
            if self.data[tw][tz][ty] & (1 << tx):
                return True
        return False

    def lock_piece(self, piece_cells, offset):
        ox, oy, oz, ow = offset
        for px, py, pz, pw in piece_cells:
            tx, ty, tz, tw = px + ox, py + oy, pz + oz, pw + ow
            self.data[tw][tz][ty] |= (1 << tx)

    def clear_full_hyper_slabs(self):
        """Clear full x·y·w layers (hyper-slabs at fixed z)."""
        cleared = []
        full_mask = (1 << self.W) - 1
        for z in range(self.H):
            is_full = True
            for w in range(self.P):
                for y in range(self.D):
                    if self.data[w][z][y] != full_mask:
                        is_full = False
                        break
                if not is_full:
                    break
            if is_full:
                cleared.append(z)

        for z_clear in sorted(cleared, reverse=True):
            for z_curr in range(z_clear, self.H + 3):
                for w in range(self.P):
                    for y in range(self.D):
                        self.data[w][z_curr][y] = self.data[w][z_curr + 1][y]
        return len(cleared)

# ---------------------------------------------------------------------------
# 6. SANITY CHECK
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"Lattice initialized. Proper rotations: {len(ROTATIONS_192)}")

    # Census smoke test
    census = run_census()
    print(f"Canonical solids: {len(census)}")

    # HYPERCRADLE verification
    hyper_ttt = TernaryMatingProduct.mate3('T', 'T', 'T')
    assert len(hyper_ttt) == 28
    print(f"HYPERCRADLE (T,T,T): V={len(hyper_ttt)} ✓")

    # Tesseract verification
    reactor = TernaryMatingProduct.mate3('O', 'O', 'O')
    assert len(reactor) == 16
    print(f"REACTOR (O,O,O): V={len(reactor)} ✓")

    # PLATE verification
    plate = TernaryMatingProduct.mate3('I', 'I', 'I')
    assert len(plate) == 64
    print(f"PLATE (I,I,I): V={len(plate)} ✓")

    # Rotation preserves cell count
    rot = transform_cells(hyper_ttt, 42)
    assert len(set(rot)) == len(hyper_ttt)
    print("Rotation uniqueness: ✓")

    print("\nP0 Sanity Check: All systems nominal.")
