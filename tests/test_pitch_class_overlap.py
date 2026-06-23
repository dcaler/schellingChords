import pytest
from schellingchords.metrics.pitch_class_overlap import PitchClassOverlap
from tests.golden import DIATONIC_CHORDS, OVERLAP_COUNTS, DISTANCES


@pytest.fixture
def metric():
    return PitchClassOverlap()


def test_identity(metric):
    """M2.T2: d(x, x) == 0.0"""
    chord = DIATONIC_CHORDS["C"]
    assert metric.distance(chord, chord) == 0.0


def test_symmetry(metric):
    """M2.T2: d(a, b) == d(b, a)"""
    a = DIATONIC_CHORDS["C"]
    b = DIATONIC_CHORDS["G"]
    assert metric.distance(a, b) == metric.distance(b, a)


def test_non_negativity(metric):
    """M2.T2: d(a, b) >= 0.0 for all pairs"""
    for pcs_a in DIATONIC_CHORDS.values():
        for pcs_b in DIATONIC_CHORDS.values():
            assert metric.distance(pcs_a, pcs_b) >= 0.0


def test_bounded_by_one(metric):
    """M2.T2: d(a, b) <= 1.0 for all pairs"""
    for pcs_a in DIATONIC_CHORDS.values():
        for pcs_b in DIATONIC_CHORDS.values():
            assert metric.distance(pcs_a, pcs_b) <= 1.0


@pytest.mark.parametrize("name_a,name_b,expected_overlap", [
    (*key, val) for key, val in OVERLAP_COUNTS.items()
])
def test_golden_overlaps(metric, name_a, name_b, expected_overlap):
    """M2.T2: Verify Jaccard distance formula: 1 - |A ∩ B| / |A ∪ B|"""
    a = DIATONIC_CHORDS[name_a]
    b = DIATONIC_CHORDS[name_b]
    union_size = len(set(a) | set(b))
    expected_dist = 1.0 - expected_overlap / union_size
    assert metric.distance(a, b) == pytest.approx(expected_dist)


@pytest.mark.parametrize("name_a,name_b,expected_dist", [
    (*key, val) for key, val in DISTANCES.items()
])
def test_golden_distances(metric, name_a, name_b, expected_dist):
    """M2.T2: Verify precomputed golden distances"""
    a = DIATONIC_CHORDS[name_a]
    b = DIATONIC_CHORDS[name_b]
    assert metric.distance(a, b) == pytest.approx(expected_dist)
