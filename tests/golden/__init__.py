"""Frozen golden values for SchellingChords metrics.

All values are hand-derived and internally consistent.
Distance formula: DISTANCE = 12 - OVERLAP
"""
from typing import Dict, List, Tuple

# Pitch class sets (0-11)
CHORD_REGISTRY: Dict[str, List[int]] = {
    "C_MAJ": [0, 4, 7],
    "A_MIN": [9, 0, 4],
    "D_MIN": [2, 5, 9],
    "G_MAJ": [7, 11, 2],
}

# Hand-computed overlaps: |A ∩ B|
# C_MAJ ∩ A_MIN = {0, 4} -> 2
# C_MAJ ∩ D_MIN = {} -> 0
# C_MAJ ∩ G_MAJ = {7} -> 1
# A_MIN ∩ D_MIN = {9} -> 1
# A_MIN ∩ G_MAJ = {} -> 0
# D_MIN ∩ G_MAJ = {2} -> 1
OVERLAP_CASES: List[Tuple[str, str, int]] = [
    ("C_MAJ", "A_MIN", 2),
    ("C_MAJ", "D_MIN", 0),
    ("C_MAJ", "G_MAJ", 1),
    ("A_MIN", "D_MIN", 1),
    ("A_MIN", "G_MAJ", 0),
    ("D_MIN", "G_MAJ", 1),
]

# Derived distances using DISTANCE = 12 - OVERLAP
# 12 - 2 = 10
# 12 - 0 = 12
# 12 - 1 = 11
# 12 - 1 = 11
# 12 - 0 = 12
# 12 - 1 = 11
DISTANCE_CASES: List[Tuple[str, str, int]] = [
    ("C_MAJ", "A_MIN", 10),
    ("C_MAJ", "D_MIN", 12),
    ("C_MAJ", "G_MAJ", 11),
    ("A_MIN", "D_MIN", 11),
    ("A_MIN", "G_MAJ", 12),
    ("D_MIN", "G_MAJ", 11),
]
