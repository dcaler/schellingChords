"""
Internal-consistency guard for the FROZEN golden values (build infrastructure).

These checks are IMPLEMENTATION-INDEPENDENT: they assert that the frozen golden
constants agree with each other and with objective ground truth (overlap counts vs
actual set intersections; window counts vs the grid vs the coordinate lists). So they
PASS at Phase 0 with no implementation, and FAIL LOUDLY if the golden module is
internally contradictory — which would otherwise silently make a downstream module
unsatisfiable (the impl can't edit a frozen test, so a wrong golden value = a hard,
unfixable block). Discovered by introspection so it survives qwen restructuring the
module or switching the distance metric; a non-vacuous run is enforced via `checks`.

Not part of any module's behavioral contract — added deliberately to catch bad freezes.
"""
from __future__ import annotations

import tests.golden as G


def _ones(grid):
    return sum(1 for row in grid for c in row if c)


def test_overlap_counts_are_true_intersections():
    """Every frozen overlap count must equal the real |a ∩ b| of the pitch-class sets."""
    chords = getattr(G, "DIATONIC_CHORDS", None)
    counts = getattr(G, "OVERLAP_COUNTS", None)
    if not chords or not counts:
        return  # nothing of this shape to validate here
    checks = 0
    for (a, b), n in counts.items():
        assert a in chords and b in chords, f"OVERLAP_COUNTS references unknown chord {a!r}/{b!r}"
        true_overlap = len(set(chords[a]) & set(chords[b]))
        assert n == true_overlap, f"OVERLAP_COUNTS[{a},{b}]={n} but |{a}∩{b}|={true_overlap}"
        checks += 1
    assert checks > 0, "OVERLAP_COUNTS present but empty"


def test_distances_consistent_and_in_range():
    """Distances must be in [0,1], agree across the DISTANCES/DISTANCES_EXACT tables,
    and hit the metric-agnostic endpoints (disjoint -> 1, identical -> 0)."""
    chords = getattr(G, "DIATONIC_CHORDS", None)
    exact = getattr(G, "DISTANCES_EXACT", None) or getattr(G, "DISTANCES", None)
    if not chords or not exact:
        return
    checks = 0
    for (a, b), d in exact.items():
        assert 0.0 <= d <= 1.0, f"distance({a},{b})={d} out of [0,1]"
        overlap = len(set(chords[a]) & set(chords[b]))
        if overlap == 0:
            assert d == 1.0, f"disjoint {a},{b} must have distance 1.0, got {d}"
        if set(chords[a]) == set(chords[b]):
            assert d == 0.0, f"identical {a},{b} must have distance 0.0, got {d}"
        checks += 1
    # the two distance tables, if both present, must agree
    d1, d2 = getattr(G, "DISTANCES", None), getattr(G, "DISTANCES_EXACT", None)
    if d1 and d2:
        assert set(d1) == set(d2), "DISTANCES and DISTANCES_EXACT have different key sets"
        for k in d1:
            assert abs(d1[k] - d2[k]) < 1e-9, f"DISTANCES vs DISTANCES_EXACT disagree at {k}"
            checks += 1
    assert checks > 0, "distance tables present but empty"


def test_window_counts_match_grid_and_coords():
    """For any *_BINARY_GRID, the occupied/vacant count constants and coordinate lists
    must match the grid; each coordinate must actually be an occupied/vacant cell."""
    grid = getattr(G, "WINDOW_BINARY_GRID", None)
    if grid is None:
        return
    cells = sum(len(row) for row in grid)
    occ = _ones(grid)
    vac = cells - occ
    checks = 0

    def check(name, expected):
        nonlocal checks
        if hasattr(G, name):
            assert getattr(G, name) == expected, f"{name}={getattr(G, name)} but grid says {expected}"
            checks += 1

    check("WINDOW_TOTAL_CELLS", cells)
    check("WINDOW_OCCUPIED_CELLS", occ)
    check("WINDOW_VACANT_CELLS", vac)

    occ_coords = getattr(G, "WINDOW_OCCUPIED_COORDS", None)
    vac_coords = getattr(G, "WINDOW_VACANT_COORDS", None)
    if occ_coords is not None:
        assert len(occ_coords) == occ, f"OCCUPIED_COORDS has {len(occ_coords)}, grid has {occ} occupied"
        for r, c in occ_coords:
            assert grid[r][c], f"OCCUPIED coord ({r},{c}) is vacant in the grid"
        checks += 1
    if vac_coords is not None:
        assert len(vac_coords) == vac, f"VACANT_COORDS has {len(vac_coords)}, grid has {vac} vacant"
        for r, c in vac_coords:
            assert not grid[r][c], f"VACANT coord ({r},{c}) is occupied in the grid"
        checks += 1
    if occ_coords is not None and vac_coords is not None:
        assert not (set(map(tuple, occ_coords)) & set(map(tuple, vac_coords))), \
            "a coordinate is listed as BOTH occupied and vacant"
        checks += 1

    assert checks > 0, "WINDOW_BINARY_GRID present but no count/coord constants to validate"
