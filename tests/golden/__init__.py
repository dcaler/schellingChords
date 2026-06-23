"""Golden values for SchellingChords tests.

All values are hand-computed and internally consistent.
Distance metric: Jaccard distance = 1 - |a ∩ b| / |a ∪ b|
Identical chords -> 0.0, disjoint chords -> 1.0
"""

# Diatonic chords in C major (pitch classes 0-11, sorted)
DIATONIC_CHORDS: dict[str, list[int]] = {
    "C": [0, 4, 7],      # C major
    "Dm": [2, 5, 9],     # D minor
    "Em": [4, 7, 11],    # E minor
    "F": [0, 5, 9],      # F major
    "G": [2, 7, 11],     # G major
    "Am": [0, 4, 9],     # A minor
    "Bdim": [2, 5, 11],  # B diminished
}

# Overlap counts: |a ∩ b| for all unordered pairs
OVERLAP_COUNTS: dict[tuple[str, str], int] = {
    ("C", "Dm"): 0,
    ("C", "Em"): 2,
    ("C", "F"): 1,
    ("C", "G"): 1,
    ("C", "Am"): 2,
    ("C", "Bdim"): 0,
    ("Dm", "Em"): 0,
    ("Dm", "F"): 2,
    ("Dm", "G"): 1,
    ("Dm", "Am"): 1,
    ("Dm", "Bdim"): 2,
    ("Em", "F"): 0,
    ("Em", "G"): 2,
    ("Em", "Am"): 1,
    ("Em", "Bdim"): 1,
    ("F", "G"): 0,
    ("F", "Am"): 2,
    ("F", "Bdim"): 1,
    ("G", "Am"): 0,
    ("G", "Bdim"): 2,
    ("Am", "Bdim"): 0,
}

# Jaccard distances: 1 - |a ∩ b| / |a ∪ b|
# Recomputed from overlaps above; all in [0.0, 1.0]
DISTANCES: dict[tuple[str, str], float] = {
    ("C", "Dm"): 1.0,       # 1 - 0/6
    ("C", "Em"): 0.5,       # 1 - 2/4
    ("C", "F"): 0.8,        # 1 - 1/5
    ("C", "G"): 0.8,        # 1 - 1/5
    ("C", "Am"): 0.5,       # 1 - 2/4
    ("C", "Bdim"): 1.0,     # 1 - 0/6
    ("Dm", "Em"): 1.0,      # 1 - 0/6
    ("Dm", "F"): 0.5,       # 1 - 2/4
    ("Dm", "G"): 0.8,       # 1 - 1/5
    ("Dm", "Am"): 0.8,      # 1 - 1/5
    ("Dm", "Bdim"): 0.5,    # 1 - 2/4
    ("Em", "F"): 1.0,       # 1 - 0/6
    ("Em", "G"): 0.5,       # 1 - 2/4
    ("Em", "Am"): 0.8,      # 1 - 1/5
    ("Em", "Bdim"): 0.8,    # 1 - 1/5
    ("F", "G"): 1.0,        # 1 - 0/6
    ("F", "Am"): 0.5,       # 1 - 2/4
    ("F", "Bdim"): 0.8,     # 1 - 1/5
    ("G", "Am"): 1.0,       # 1 - 0/6
    ("G", "Bdim"): 0.5,     # 1 - 2/4
    ("Am", "Bdim"): 1.0,    # 1 - 0/6
}

# 1D window fixture constants (bars_per_window=4, 4 beats/bar)
WINDOW_TOTAL_SLOTS: int = 16
WINDOW_SLOTS: list[int] = [1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0]
WINDOW_OCCUPIED_INDICES: list[int] = [0, 1, 2, 4, 5, 6, 8, 9, 10, 11, 13, 14]
WINDOW_OCCUPIED_SLOTS: int = len(WINDOW_OCCUPIED_INDICES)
WINDOW_VACANT_SLOTS: int = WINDOW_TOTAL_SLOTS - WINDOW_OCCUPIED_SLOTS

# Freeze reconcile (Cale+Claude): names later frozen tests import (test_golden.py,
# test_config.py) that the P0 author omitted. DERIVED from WINDOW_SLOTS so they cannot
# disagree with it; tests/golden/test_golden_consistency.py validates WINDOW_VACANT_INDICES.
WINDOW_VACANT_INDICES: list[int] = [i for i, s in enumerate(WINDOW_SLOTS) if not s]
WINDOW_OCCUPIED_COUNT: int = WINDOW_OCCUPIED_SLOTS   # alias used by test_golden.py
WINDOW_VACANT_COUNT: int = WINDOW_VACANT_SLOTS        # alias used by test_golden.py
