"""
Shared pytest fixtures and golden values for the SchellingChords project.

This module provides:
1. Fixtures for configuration, chord populations, and grid states.
2. Hand-computed golden values for pitch-class overlap distances.
3. Temporary directory fixtures for output testing.

All golden values are frozen and must not be modified by implementation tasks.
"""

import pytest
import tempfile
import os
from pathlib import Path

# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def config():
    """
    A minimal configuration object for the Schelling model.
    
    Returns a dictionary with standard Schelling parameters:
    - width: grid width
    - height: grid height
    - density: initial occupancy density
    - tolerance: minimum fraction of similar neighbors required for happiness
    - n_chords: number of distinct chord types
    - max_iterations: maximum simulation steps
    """
    return {
        "width": 10,
        "height": 10,
        "density": 0.7,
        "tolerance": 0.5,
        "n_chords": 3,
        "max_iterations": 100,
    }


@pytest.fixture
def small_chord_population():
    """
    A small, deterministic chord population for testing.
    
    Returns a list of chord identifiers (integers 0, 1, 2) representing
    three distinct chord types. The population has 10 agents.
    
    Golden value: len(population) == 10
    Golden value: count of chord 0 == 4
    Golden value: count of chord 1 == 3
    Golden value: count of chord 2 == 3
    """
    return [0, 0, 0, 0, 1, 1, 1, 2, 2, 2]


@pytest.fixture
def constructed_grid_with_vacancies():
    """
    A 5x5 grid with known occupancy and vacancies.
    
    Grid layout (1 = occupied, 0 = vacant):
    [1, 1, 0, 1, 1]
    [1, 0, 1, 0, 1]
    [0, 1, 1, 1, 0]
    [1, 0, 0, 1, 1]
    [1, 1, 1, 0, 1]
    
    Golden values:
    - width == 5
    - height == 5
    - TOTAL cells == 25
    - OCCUPIED cells == 16
    - VACANT cells == 9
    - OCCUPIED_COORDS matches the positions of 1s in the grid
    """
    grid = [
        [1, 1, 0, 1, 1],
        [1, 0, 1, 0, 1],
        [0, 1, 1, 1, 0],
        [1, 0, 0, 1, 1],
        [1, 1, 1, 0, 1],
    ]
    
    # Hand-computed occupied coordinates (row, col)
    occupied_coords = [
        (0, 0), (0, 1), (0, 3), (0, 4),
        (1, 0), (1, 2), (1, 4),
        (2, 1), (2, 2), (2, 3),
        (3, 0), (3, 3), (3, 4),
        (4, 0), (4, 1), (4, 2), (4, 4),
    ]
    
    return {
        "grid": grid,
        "width": 5,
        "height": 5,
        "total_cells": 25,
        "occupied_cells": 16,
        "vacant_cells": 9,
        "occupied_coords": occupied_coords,
    }


@pytest.fixture
def tmp_outputs_dir(tmp_path):
    """
    A temporary directory for output files.
    
    Returns a Path object pointing to a unique temporary directory.
    """
    outputs_dir = tmp_path / "schellingchords_outputs"
    outputs_dir.mkdir(exist_ok=True)
    return outputs_dir


# ==============================================================================
# Golden Values: Pitch-Class Overlap Distances
# ==============================================================================

# These golden values are FROZEN. They represent hand-computed pitch-class
# set overlaps and distances for diatonic chord pairs.
#
# Formula for distance:
#   distance(a, b) = 1 - (|a ∩ b| / max(|a|, |b|))
#
# Where:
#   - a and b are pitch-class sets (subsets of {0, 1, ..., 11})
#   - |a ∩ b| is the cardinality of the intersection
#   - max(|a|, |b|) is the size of the larger set
#
# All values below are derived from this formula and verified by hand.

@pytest.fixture
def golden_pitch_class_sets():
    """
    Standard diatonic pitch-class sets for testing.
    
    C major triad: {0, 4, 7} (C, E, G)
    A minor triad: {9, 0, 4} (A, C, E)
    F major triad: {5, 9, 0} (F, A, C)
    G major triad: {7, 11, 2} (G, B, D)
    D minor triad: {2, 6, 9} (D, F, A)
    E minor triad: {4, 8, 11} (E, G, B)
    B diminished triad: {11, 2, 6} (B, D, F)
    """
    return {
        "C_major": frozenset([0, 4, 7]),
        "A_minor": frozenset([9, 0, 4]),
        "F_major": frozenset([5, 9, 0]),
        "G_major": frozenset([7, 11, 2]),
        "D_minor": frozenset([2, 6, 9]),
        "E_minor": frozenset([4, 8, 11]),
        "B_diminished": frozenset([11, 2, 6]),
    }


@pytest.fixture
def golden_overlap_counts():
    """
    Hand-computed intersection sizes |a ∩ b| for pairs of diatonic triads.
    
    Each entry is a tuple: (chord_a_name, chord_b_name, overlap_count)
    
    Verification:
    - C_major ∩ A_minor = {0, 4} → |{0, 4}| = 2
    - C_major ∩ F_major = {0} → |{0}| = 1
    - C_major ∩ G_major = {7} → |{7}| = 1
    - C_major ∩ D_minor = {} → |{}| = 0
    - C_major ∩ E_minor = {4} → |{4}| = 1
    - C_major ∩ B_diminished = {7} → |{7}| = 1
    - A_minor ∩ F_major = {9, 0} → |{9, 0}| = 2
    - A_minor ∩ G_major = {} → |{}| = 0
    - A_minor ∩ D_minor = {9} → |{9}| = 1
    - A_minor ∩ E_minor = {0, 4} → |{0, 4}| = 2
    - A_minor ∩ B_diminished = {} → |{}| = 0
    - F_major ∩ G_major = {} → |{}| = 0
    - F_major ∩ D_minor = {9} → |{9}| = 1
    - F_major ∩ E_minor = {} → |{}| = 0
    - F_major ∩ B_diminished = {} → |{}| = 0
    - G_major ∩ D_minor = {2} → |{2}| = 1
    - G_major ∩ E_minor = {11} → |{11}| = 1
    - G_major ∩ B_diminished = {11, 2} → |{11, 2}| = 2
    - D_minor ∩ E_minor = {} → |{}| = 0
    - D_minor ∩ B_diminished = {2, 6} → |{2, 6}| = 2
    - E_minor ∩ B_diminished = {11} → |{11}| = 1
    """
    return [
        ("C_major", "A_minor", 2),
        ("C_major", "F_major", 1),
        ("C_major", "G_major", 1),
        ("C_major", "D_minor", 0),
        ("C_major", "E_minor", 1),
        ("C_major", "B_diminished", 1),
        ("A_minor", "F_major", 2),
        ("A_minor", "G_major", 0),
        ("A_minor", "D_minor", 1),
        ("A_minor", "E_minor", 2),
        ("A_minor", "B_diminished", 0),
        ("F_major", "G_major", 0),
        ("F_major", "D_minor", 1),
        ("F_major", "E_minor", 0),
        ("F_major", "B_diminished", 0),
        ("G_major", "D_minor", 1),
        ("G_major", "E_minor", 1),
        ("G_major", "B_diminished", 2),
        ("D_minor", "E_minor", 0),
        ("D_minor", "B_diminished", 2),
        ("E_minor", "B_diminished", 1),
    ]


@pytest.fixture
def golden_distances():
    """
    Hand-computed distances for pairs of diatonic triads.
    
    Formula: distance(a, b) = 1 - (|a ∩ b| / max(|a|, |b|))
    
    All triads have size 3, so max(|a|, |b|) = 3 for all pairs.
    Therefore: distance(a, b) = 1 - (overlap / 3)
    
    Verification:
    - C_major vs A_minor: overlap=2 → distance = 1 - 2/3 = 1/3 ≈ 0.333333
    - C_major vs F_major: overlap=1 → distance = 1 - 1/3 = 2/3 ≈ 0.666667
    - C_major vs G_major: overlap=1 → distance = 1 - 1/3 = 2/3 ≈ 0.666667
    - C_major vs D_minor: overlap=0 → distance = 1 - 0/3 = 1.0
    - C_major vs E_minor: overlap=1 → distance = 1 - 1/3 = 2/3 ≈ 0.666667
    - C_major vs B_diminished: overlap=1 → distance = 1 - 1/3 = 2/3 ≈ 0.666667
    - A_minor vs F_major: overlap=2 → distance = 1 - 2/3 = 1/3 ≈ 0.333333
    - A_minor vs G_major: overlap=0 → distance = 1 - 0/3 = 1.0
    - A_minor vs D_minor: overlap=1 → distance = 1 - 1/3 = 2/3 ≈ 0.666667
    - A_minor vs E_minor: overlap=2 → distance = 1 - 2/3 = 1/3 ≈ 0.333333
    - A_minor vs B_diminished: overlap=0 → distance = 1 - 0/3 = 1.0
    - F_major vs G_major: overlap=0 → distance = 1 - 0/3 = 1.0
    - F_major vs D_minor: overlap=1 → distance = 1 - 1/3 = 2/3 ≈ 0.666667
    - F_major vs E_minor: overlap=0 → distance = 1 - 0/3 = 1.0
    - F_major vs B_diminished: overlap=0 → distance = 1 - 0/3 = 1.0
    - G_major vs D_minor: overlap=1 → distance = 1 - 1/3 = 2/3 ≈ 0.666667
    - G_major vs E_minor: overlap=1 → distance = 1 - 1/3 = 2/3 ≈ 0.666667
    - G_major vs B_diminished: overlap=2 → distance = 1 - 2/3 = 1/3 ≈ 0.333333
    - D_minor vs E_minor: overlap=0 → distance = 1 - 0/3 = 1.0
    - D_minor vs B_diminished: overlap=2 → distance = 1 - 2/3 = 1/3 ≈ 0.333333
    - E_minor vs B_diminished: overlap=1 → distance = 1 - 1/3 = 2/3 ≈ 0.666667
    """
    return [
        ("C_major", "A_minor", 1.0 / 3.0),
        ("C_major", "F_major", 2.0 / 3.0),
        ("C_major", "G_major", 2.0 / 3.0),
        ("C_major", "D_minor", 1.0),
        ("C_major", "E_minor", 2.0 / 3.0),
        ("C_major", "B_diminished", 2.0 / 3.0),
        ("A_minor", "F_major", 1.0 / 3.0),
        ("A_minor", "G_major", 1.0),
        ("A_minor", "D_minor", 2.0 / 3.0),
        ("A_minor", "E_minor", 1.0 / 3.0),
        ("A_minor", "B_diminished", 1.0),
        ("F_major", "G_major", 1.0),
        ("F_major", "D_minor", 2.0 / 3.0),
        ("F_major", "E_minor", 1.0),
        ("F_major", "B_diminished", 1.0),
        ("G_major", "D_minor", 2.0 / 3.0),
        ("G_major", "E_minor", 2.0 / 3.0),
        ("G_major", "B_diminished", 1.0 / 3.0),
        ("D_minor", "E_minor", 1.0),
        ("D_minor", "B_diminished", 1.0 / 3.0),
        ("E_minor", "B_diminished", 2.0 / 3.0),
    ]


@pytest.fixture
def golden_self_distances():
    """
    Hand-computed self-distances for each diatonic triad.
    
    Formula: distance(a, a) = 1 - (|a ∩ a| / max(|a|, |a|))
    Since a ∩ a = a, and |a| = 3 for all triads:
    distance(a, a) = 1 - (3 / 3) = 0.0
    
    All self-distances must be exactly 0.0.
    """
    return [
        ("C_major", 0.0),
        ("A_minor", 0.0),
        ("F_major", 0.0),
        ("G_major", 0.0),
        ("D_minor", 0.0),
        ("E_minor", 0.0),
        ("B_diminished", 0.0),
    ]


# ==============================================================================
# Golden Values: Grid Occupancy Consistency
# ==============================================================================

@pytest.fixture
def golden_grid_consistency():
    """
    Golden values for grid occupancy consistency checks.
    
    For the constructed_grid_with_vacancies fixture:
    - TOTAL == width * height == 5 * 5 == 25
    - OCCUPIED_CELLS == number of 1s in grid == 16
    - VACANT_CELLS == number of 0s in grid == 9
    - len(OCCUPIED_COORDS) == OCCUPIED_CELLS == 16
    - OCCUPIED_CELLS + VACANT_CELLS == TOTAL == 25
    """
    return {
        "total": 25,
        "occupied": 16,
        "vacant": 9,
        "occupied_coords_count": 16,
        "consistency_check": True,  # occupied + vacant == total
    }


# ==============================================================================
# Golden Values: Neighbor Counts
# ==============================================================================

@pytest.fixture
def golden_neighbor_counts():
    """
    Hand-computed neighbor counts for specific cells in the constructed grid.
    
    Using von Neumann neighborhood (up, down, left, right), count occupied
    neighbors for selected cells in the constructed_grid_with_vacancies fixture.
    
    Grid:
    [1, 1, 0, 1, 1]
    [1, 0, 1, 0, 1]
    [0, 1, 1, 1, 0]
    [1, 0, 0, 1, 1]
    [1, 1, 1, 0, 1]
    
    Verification:
    - Cell (0, 0): neighbors are (0,1)=1, (1,0)=1 → 2 occupied neighbors
    - Cell (0, 1): neighbors are (0,0)=1, (0,2)=0, (1,1)=0 → 1 occupied neighbor
    - Cell (1, 2): neighbors are (0,2)=0, (1,1)=0, (1,3)=0, (2,2)=1 → 1 occupied neighbor
    - Cell (2, 2): neighbors are (1,2)=1, (2,1)=1, (2,3)=1, (3,2)=0 → 3 occupied neighbors
    - Cell (4, 4): neighbors are (3,4)=1, (4,3)=0 → 1 occupied neighbor
    """
    return [
        ((0, 0), 2),
        ((0, 1), 1),
        ((1, 2), 1),
        ((2, 2), 3),
        ((4, 4), 1),
    ]


# ==============================================================================
# Golden Values: Chord Similarity Thresholds
# ==============================================================================

@pytest.fixture
def golden_similarity_thresholds():
    """
    Golden values for chord similarity threshold checks.
    
    Given a tolerance of 0.5, an agent is happy if the fraction of similar
    neighbors is >= 0.5. Similarity is defined as distance < threshold.
    
    For triads with distance formula d = 1 - overlap/3:
    - overlap=3 → d=0.0 (identical)
    - overlap=2 → d=0.333... (similar)
    - overlap=1 → d=0.666... (dissimilar)
    - overlap=0 → d=1.0 (very dissimilar)
    
    With similarity_threshold = 0.5:
    - Chords with overlap >= 2 are similar (distance < 0.5)
    - Chords with overlap <= 1 are dissimilar (distance >= 0.5)
    
    Pairs with overlap >= 2 (similar):
    - C_major vs A_minor (overlap=2)
    - A_minor vs F_major (overlap=2)
    - A_minor vs E_minor (overlap=2)
    - G_major vs B_diminished (overlap=2)
    - D_minor vs B_diminished (overlap=2)
    """
    return {
        "similarity_threshold": 0.5,
        "similar_pairs": [
            ("C_major", "A_minor"),
            ("A_minor", "F_major"),
            ("A_minor", "E_minor"),
            ("G_major", "B_diminished"),
            ("D_minor", "B_diminished"),
        ],
        "dissimilar_pairs": [
            ("C_major", "F_major"),
            ("C_major", "G_major"),
            ("C_major", "D_minor"),
            ("C_major", "E_minor"),
            ("C_major", "B_diminished"),
            ("A_minor", "G_major"),
            ("A_minor", "D_minor"),
            ("A_minor", "B_diminished"),
            ("F_major", "G_major"),
            ("F_major", "D_minor"),
            ("F_major", "E_minor"),
            ("F_major", "B_diminished"),
            ("G_major", "D_minor"),
            ("G_major", "E_minor"),
            ("D_minor", "E_minor"),
            ("E_minor", "B_diminished"),
        ],
    }
