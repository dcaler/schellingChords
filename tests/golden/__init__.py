"""Frozen golden values for M0 consistency checks."""
from typing import Dict, List, Tuple

# Diatonic major triads in C major (pitch classes 0..11)
DIATONIC_CHORDS: Dict[str, List[int]] = {
    "C": [0, 4, 7],
    "Dm": [2, 5, 9],
    "Em": [4, 7, 10],
}

# Intersection sizes |a ∩ b|
OVERLAP_COUNTS: Dict[Tuple[str, str], int] = {
    ("C", "Dm"): 0,
    ("C", "Em"): 2,
    ("Dm", "Em"): 0,
}

# Jaccard distance: 1 - |a ∩ b| / |a ∪ b|, normalized to [0, 1]
DISTANCES: Dict[Tuple[str, str], float] = {
    ("C", "Dm"): 1.0,
    ("C", "Em"): 0.5,
    ("Dm", "Em"): 1.0,
}

# 1D window fixture: 4 bars * 4 beats/bar = 16 slots
WINDOW_TOTAL_SLOTS: int = 16
WINDOW_SLOTS: List[int] = [1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 0]
WINDOW_OCCUPIED_INDICES: List[int] = [0, 1, 2, 4, 5, 6, 7, 9, 10, 11, 12, 13]
WINDOW_VACANT_INDICES: List[int] = [3, 8, 14, 15]
WINDOW_OCCUPIED_SLOTS: int = 12
WINDOW_VACANT_SLOTS: int = 4
