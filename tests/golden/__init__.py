"""Golden constants for M1 chord tests.

All values are hand-computed and internally consistent.
Distance metric: Jaccard distance = 1 - |a ∩ b| / |a ∪ b|, normalised to [0,1].
"""

# Diatonic triads of C major: name -> sorted pitch classes (0-11)
# I=C, ii=Dm, iii=Em, IV=F, V=G, vi=Am, vii°=Bdim
DIATONIC_CHORDS: dict[str, list[int]] = {
    "I": [0, 4, 7],
    "ii": [2, 5, 9],
    "iii": [4, 7, 11],
    "IV": [0, 5, 9],
    "V": [2, 7, 11],
    "vi": [0, 4, 9],
    "vii°": [2, 5, 11],
}

# Overlap counts: |a ∩ b| for each pair (keys sorted lexicographically by name)
OVERLAP_COUNTS: dict[tuple[str, str], int] = {
    ("I", "IV"): 1,
    ("I", "V"): 1,
    ("I", "ii"): 0,
    ("I", "iii"): 2,
    ("I", "vi"): 2,
    ("I", "vii°"): 0,
    ("IV", "V"): 0,
    ("IV", "ii"): 2,
    ("IV", "iii"): 0,
    ("IV", "vi"): 2,
    ("IV", "vii°"): 1,
    ("V", "ii"): 1,
    ("V", "iii"): 2,
    ("V", "vi"): 0,
    ("V", "vii°"): 2,
    ("ii", "iii"): 0,
    ("ii", "vi"): 1,
    ("ii", "vii°"): 2,
    ("iii", "vi"): 1,
    ("iii", "vii°"): 1,
    ("vi", "vii°"): 0,
}

# Jaccard distances: distance(a,b) = 1 - |a ∩ b| / |a ∪ b|
# All triads have cardinality 3, so |a ∪ b| = 6 - |a ∩ b|
# overlap=0 -> 1-0/6=1.0, overlap=1 -> 1-1/5=0.8, overlap=2 -> 1-2/4=0.5
DISTANCES: dict[tuple[str, str], float] = {
    ("I", "IV"): 0.8,
    ("I", "V"): 0.8,
    ("I", "ii"): 1.0,
    ("I", "iii"): 0.5,
    ("I", "vi"): 0.5,
    ("I", "vii°"): 1.0,
    ("IV", "V"): 1.0,
    ("IV", "ii"): 0.5,
    ("IV", "iii"): 1.0,
    ("IV", "vi"): 0.5,
    ("IV", "vii°"): 0.8,
    ("V", "ii"): 0.8,
    ("V", "iii"): 0.5,
    ("V", "vi"): 1.0,
    ("V", "vii°"): 0.5,
    ("ii", "iii"): 1.0,
    ("ii", "vi"): 0.8,
    ("ii", "vii°"): 0.5,
    ("iii", "vi"): 0.8,
    ("iii", "vii°"): 0.8,
    ("vi", "vii°"): 1.0,
}

# 1D window fixture constants (default 4 bars of 4/4)
WINDOW_TOTAL_SLOTS: int = 16  # 4 bars * 4 beats
WINDOW_SLOTS: list[int] = [1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0]  # 10 occupied, 6 vacant
WINDOW_OCCUPIED_INDICES: list[int] = [0, 2, 3, 5, 6, 8, 9, 11, 13, 14]
WINDOW_VACANT_INDICES: list[int] = [1, 4, 7, 10, 12, 15]
WINDOW_OCCUPIED_SLOTS: int = 10
WINDOW_VACANT_SLOTS: int = 6
