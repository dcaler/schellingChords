# Golden values for SchellingChords M8 acceptance
# Chords: C, Dm, F, G (major/minor triads in C major)
# Pitch classes: 0=C, 1=C#, ..., 11=B
DIATONIC_CHORDS = {
    "C": [0, 4, 7],
    "Dm": [2, 5, 9],
    "F": [0, 5, 8],
    "G": [2, 7, 10],
}

# Jaccard distance: 1 - |A ∩ B| / |A ∪ B|
# All chords have size 3. Union size = 6 - overlap.
# Identical chords -> 0.0, disjoint chords -> 1.0
OVERLAP_COUNTS = {
    ("C", "Dm"): 0,
    ("C", "F"): 1,
    ("C", "G"): 1,
    ("Dm", "F"): 1,
    ("Dm", "G"): 1,
    ("F", "G"): 0,
}

DISTANCES = {
    ("C", "Dm"): 1.0,
    ("C", "F"): 0.8,
    ("C", "G"): 0.8,
    ("Dm", "F"): 0.8,
    ("Dm", "G"): 0.8,
    ("F", "G"): 1.0,
}
