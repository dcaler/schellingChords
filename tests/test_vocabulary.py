"""Frozen tests for M1.T2: Diatonic vocabulary, registry, and select_types.

Tests assert concrete golden pitch-class sets, voicings, registry structure,
and selection behavior with validation.
"""

import pytest
from tests.golden import DIATONIC_CHORDS, OVERLAP_COUNTS, DISTANCES


@pytest.fixture
def vocab_module():
    """Import vocabulary module; skip if not yet implemented."""
    try:
        from schellingchords import vocabulary
        return vocabulary
    except ImportError:
        pytest.skip("schellingchords.vocabulary not yet implemented")


@pytest.fixture
def diatonic_major(vocab_module):
    return vocab_module.diatonic_major


@pytest.fixture
def VOCABULARIES(vocab_module):
    return vocab_module.VOCABULARIES


@pytest.fixture
def select_types(vocab_module):
    return vocab_module.select_types


class TestDiatonicMajor:
    """diatonic_major() must return exactly 7 diatonic triads of C major."""

    def test_returns_seven_chords(self, diatonic_major):
        chords = diatonic_major()
        assert len(chords) == 7

    def test_chord_names_match_golden(self, diatonic_major):
        chords = diatonic_major()
        names = {c.name for c in chords}
        assert names == set(DIATONIC_CHORDS.keys())

    @pytest.mark.parametrize("name,pitch_classes", [
        ("C", [0, 4, 7]),
        ("Dm", [2, 5, 9]),
        ("Em", [4, 7, 11]),
        ("F", [0, 5, 9]),
        ("G", [2, 7, 11]),
        ("Am", [0, 4, 9]),
        ("Bdim", [2, 5, 11]),
    ])
    def test_pitch_classes_match_golden(self, diatonic_major, name, pitch_classes):
        chords = diatonic_major()
        chord_by_name = {c.name: c for c in chords}
        c = chord_by_name[name]
        assert sorted(c.pitch_classes) == pitch_classes

    def test_all_are_triads(self, diatonic_major):
        chords = diatonic_major()
        for c in chords:
            assert len(c.pitch_classes) == 3

    def test_voicings_consistent_with_pitch_classes(self, diatonic_major):
        chords = diatonic_major()
        for c in chords:
            reduced = frozenset(midi % 12 for midi in c.midi_voicing)
            assert reduced == c.pitch_classes

    def test_voicings_are_octave_4_or_higher(self, diatonic_major):
        chords = diatonic_major()
        for c in chords:
            assert all(midi >= 60 for midi in c.midi_voicing)


class TestVocabulariesRegistry:
    """VOCABULARIES must be a dict keyed by vocabulary name."""

    def test_is_dict(self, VOCABULARIES):
        assert isinstance(VOCABULARIES, dict)

    def test_contains_diatonic_major(self, VOCABULARIES):
        assert "diatonic_major" in VOCABULARIES

    def test_diatonic_major_callable(self, VOCABULARIES):
        assert callable(VOCABULARIES["diatonic_major"])

    def test_registry_returns_same_chords_as_function(self, VOCABULARIES, diatonic_major):
        chords_from_registry = VOCABULARIES["diatonic_major"]()
        chords_from_func = diatonic_major()
        assert len(chords_from_registry) == len(chords_from_func)
        names_registry = {c.name for c in chords_from_registry}
        names_func = {c.name for c in chords_from_func}
        assert names_registry == names_func


class TestSelectTypes:
    """select_types(vocabulary, n, rng) must return n distinct valid Chords."""

    def test_returns_n_chords(self, select_types, diatonic_major):
        import random
        rng = random.Random(42)
        chords = select_types(diatonic_major, n=4, rng=rng)
        assert len(chords) == 4

    def test_all_distinct(self, select_types, diatonic_major):
        import random
        rng = random.Random(42)
        chords = select_types(diatonic_major, n=5, rng=rng)
        assert len(chords) == len(set(chords))

    def test_all_from_vocabulary(self, select_types, diatonic_major):
        import random
        rng = random.Random(42)
        vocab_chords = diatonic_major()
        vocab_names = {c.name for c in vocab_chords}
        selected = select_types(diatonic_major, n=3, rng=rng)
        for c in selected:
            assert c.name in vocab_names

    def test_validates_n_minimum(self, select_types, diatonic_major):
        import random
        rng = random.Random(42)
        with pytest.raises(ValueError):
            select_types(diatonic_major, n=1, rng=rng)

    def test_validates_n_maximum(self, select_types, diatonic_major):
        import random
        rng = random.Random(42)
        with pytest.raises(ValueError):
            select_types(diatonic_major, n=8, rng=rng)

    def test_n_equals_vocabulary_size(self, select_types, diatonic_major):
        import random
        rng = random.Random(42)
        chords = select_types(diatonic_major, n=7, rng=rng)
        assert len(chords) == 7
        assert len(set(chords)) == 7

    def test_deterministic_with_same_seed(self, select_types, diatonic_major):
        import random
        rng1 = random.Random(123)
        rng2 = random.Random(123)
        chords1 = select_types(diatonic_major, n=4, rng=rng1)
        chords2 = select_types(diatonic_major, n=4, rng=rng2)
        assert chords1 == chords2

    def test_chords_are_immutable_instances(self, select_types, diatonic_major):
        import random
        rng = random.Random(42)
        chords = select_types(diatonic_major, n=3, rng=rng)
        for c in chords:
            assert isinstance(c.pitch_classes, frozenset)
            assert isinstance(c.midi_voicing, tuple)


class TestOverlapAndDistanceGolden:
    """Verify overlap counts and Jaccard distances against golden values."""

    def test_overlap_counts_match_golden(self, diatonic_major):
        chords = diatonic_major()
        chord_by_name = {c.name: c for c in chords}
        for (name_a, name_b), expected_overlap in OVERLAP_COUNTS.items():
            a = chord_by_name[name_a]
            b = chord_by_name[name_b]
            actual_overlap = len(a.pitch_classes & b.pitch_classes)
            assert actual_overlap == expected_overlap, f"Overlap mismatch for ({name_a}, {name_b})"

    def test_distances_match_golden(self, diatonic_major):
        chords = diatonic_major()
        chord_by_name = {c.name: c for c in chords}
        for (name_a, name_b), expected_dist in DISTANCES.items():
            a = chord_by_name[name_a]
            b = chord_by_name[name_b]
            intersection = len(a.pitch_classes & b.pitch_classes)
            union = len(a.pitch_classes | b.pitch_classes)
            # Jaccard distance: 1 - |a ∩ b| / |a ∪ b|
            actual_dist = 1.0 - intersection / union
            assert abs(actual_dist - expected_dist) < 1e-9, f"Distance mismatch for ({name_a}, {name_b})"
