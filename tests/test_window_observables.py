import pytest
from tests.golden import DISTANCES

# 1D Window fixture constants (4 bars * 4 beats/bar = 16 slots)
WINDOW_TOTAL_SLOTS = 16
WINDOW_SLOTS = [1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0]
WINDOW_OCCUPIED_INDICES = [0, 1, 2, 4, 5, 7, 8, 10, 12, 14]
WINDOW_OCCUPIED_SLOTS = len(WINDOW_OCCUPIED_INDICES)
WINDOW_CHORD_MAP = {
    0: "C", 1: "C", 2: "C",
    4: "Em", 5: "Em",
    7: "Dm", 8: "Dm",
    10: "C",
    12: "Em", 14: "Em",
}

# Invariant checks for fixture consistency
assert WINDOW_TOTAL_SLOTS == 4 * 4 == len(WINDOW_SLOTS)
assert WINDOW_OCCUPIED_SLOTS == len(WINDOW_OCCUPIED_INDICES)
assert sum(WINDOW_SLOTS) == WINDOW_OCCUPIED_SLOTS
assert WINDOW_TOTAL_SLOTS == WINDOW_OCCUPIED_SLOTS + (WINDOW_TOTAL_SLOTS - WINDOW_OCCUPIED_SLOTS)

@pytest.mark.parametrize("tolerance, expected_seg, expected_reg", [
    (0.6, 0.8, 6),
])
def test_segregation_index_and_region_count(tolerance, expected_seg, expected_reg):
    from schellingchords.observables import segregation_index, region_count

    # Build 1D window state: chord name or None for rests
    window_state = [WINDOW_CHORD_MAP.get(i) for i in range(WINDOW_TOTAL_SLOTS)]
    # Freeze reconcile (Cale+Claude): DISTANCES is a half-matrix (each unordered
    # pair stored once, no diagonal), so a raw DISTANCES.get((a,b),1.0) is neither
    # reflexive (d(a,a) -> 1.0) nor symmetric (d(Em,C) -> 1.0 while d(C,Em)=0.5).
    # The golden expected values (0.8, 6) were computed under the TRUE Jaccard
    # metric, so the adapter must present one: identity -> 0.0, and try both orders.
    metric = lambda a, b: 0.0 if a == b else DISTANCES.get((a, b), DISTANCES.get((b, a), 1.0))

    seg = segregation_index(window_state, metric, tolerance, radius=2)
    reg = region_count(window_state, metric, tolerance)

    assert seg == pytest.approx(expected_seg, abs=1e-6)
    assert reg == expected_reg
