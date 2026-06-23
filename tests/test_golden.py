import pytest
from tests.golden import (
    DIATONIC_CHORDS, OVERLAP_COUNTS, DISTANCES,
    WINDOW_TOTAL_SLOTS, WINDOW_SLOTS, WINDOW_OCCUPIED_INDICES,
    WINDOW_VACANT_INDICES, WINDOW_OCCUPIED_COUNT, WINDOW_VACANT_COUNT
)


class TestGoldenChords:
    """Validate hand-computed chord data and metric consistency."""

    def test_chord_cardinality_and_range(self):
        """All diatonic triads must have exactly 3 pitch classes in 0..11."""
        for name, pcs in DIATONIC_CHORDS.items():
            assert len(pcs) == 3, f"{name} has {len(pcs)} pitch classes"
            assert pcs == sorted(pcs), f"{name} pitch classes not sorted"
            assert all(0 <= pc <= 11 for pc in pcs), f"{name} has out-of-range pitch classes"

    def test_overlap_counts_match_intersections(self):
        """OVERLAP_COUNTS must equal actual set intersection sizes."""
        for (a, b), expected in OVERLAP_COUNTS.items():
            actual = len(set(DIATONIC_CHORDS[a]) & set(DIATONIC_CHORDS[b]))
            assert actual == expected, f"Overlap mismatch for ({a}, {b}): {actual} != {expected}"

    def test_distances_follow_jaccard_formula(self):
        """DISTANCES must follow: 1 - |a∩b| / |a∪b|"""
        for (a, b), expected in DISTANCES.items():
            union = len(set(DIATONIC_CHORDS[a]) | set(DIATONIC_CHORDS[b]))
            inter = len(set(DIATONIC_CHORDS[a]) & set(DIATONIC_CHORDS[b]))
            actual = 1.0 - inter / union
            assert abs(actual - expected) < 1e-9, f"Distance mismatch for ({a}, {b})"

    @pytest.mark.parametrize("chord_a,chord_b,expected_dist", [
        (*key, val) for key, val in DISTANCES.items()
    ])
    def test_parametrized_jaccard_distances(self, chord_a, chord_b, expected_dist):
        """Parametrized verification of all pairwise distances."""
        union = len(set(DIATONIC_CHORDS[chord_a]) | set(DIATONIC_CHORDS[chord_b]))
        inter = len(set(DIATONIC_CHORDS[chord_a]) & set(DIATONIC_CHORDS[chord_b]))
        actual = 1.0 - inter / union
        assert abs(actual - expected_dist) < 1e-9


class TestGoldenWindow:
    """Validate 1D window fixture consistency."""

    def test_slot_array_length(self):
        assert len(WINDOW_SLOTS) == WINDOW_TOTAL_SLOTS

    def test_occupied_count_matches_sum(self):
        assert sum(WINDOW_SLOTS) == WINDOW_OCCUPIED_COUNT

    def test_vacant_count_complement(self):
        assert WINDOW_OCCUPIED_COUNT + WINDOW_VACANT_COUNT == WINDOW_TOTAL_SLOTS

    def test_indices_cover_all_slots(self):
        all_indices = set(WINDOW_OCCUPIED_INDICES) | set(WINDOW_VACANT_INDICES)
        assert all_indices == set(range(WINDOW_TOTAL_SLOTS))

    def test_slot_values_match_indices(self):
        for i in WINDOW_OCCUPIED_INDICES:
            assert WINDOW_SLOTS[i] == 1
        for i in WINDOW_VACANT_INDICES:
            assert WINDOW_SLOTS[i] == 0


class TestModelIntegration:
    """Tests that will FAIL until schellingchords implementation exists."""

    def test_config_fixture_fields(self, config):
        """Verify Config dataclass has exactly the specified fields."""
        assert config.n_chord_types == 7
        assert config.bars_per_window == 4
        assert config.vacancy_fraction == 0.25
        assert config.tolerance == 0.5
        assert config.happiness == 0.6
        assert config.radius == 2
        assert config.tempo_bpm == 120
        assert config.seed == 42

    def test_model_initialization(self, config, chord_population, window_with_vacancies):
        """Model should be instantiable with config and population data."""
        from schellingchords.model import SchellingChordModel
        model = SchellingChordModel(config)
        assert model is not None

    def test_model_step(self, config, chord_population, window_with_vacancies):
        """Model step should execute without error."""
        from schellingchords.model import SchellingChordModel
        model = SchellingChordModel(config)
        model.step()
