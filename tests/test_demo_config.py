import pytest
from tests.golden import DIATONIC_CHORDS, OVERLAP_COUNTS, DISTANCES


@pytest.fixture
def demo_config_kwargs():
    """Exactly the 8 Config fields for the demo run (happiness is a [0,1] fraction)."""
    return {
        "n_chord_types": 4,
        "bars_per_window": 4,
        "vacancy_fraction": 0.25,
        "tolerance": 0.5,
        "happiness": 0.6,
        "radius": 2,
        "tempo_bpm": 120,
        "seed": 42,
    }


class TestDemoConfig:
    def test_config_fields_exist(self, demo_config_kwargs):
        expected_fields = {
            "n_chord_types", "bars_per_window", "vacancy_fraction",
            "tolerance", "happiness", "radius", "tempo_bpm", "seed"
        }
        assert set(demo_config_kwargs.keys()) == expected_fields

    def test_config_instantiation(self, demo_config_kwargs):
        from schellingchords.config import Config
        cfg = Config(**demo_config_kwargs)
        assert cfg.bars_per_window == 4
        assert cfg.vacancy_fraction == 0.25
        assert cfg.seed == 42
        assert cfg.n_chord_types == 4

    @pytest.mark.parametrize("chord_name,pitch_classes", list(DIATONIC_CHORDS.items()))
    def test_chord_pitch_classes(self, chord_name, pitch_classes):
        assert len(pitch_classes) == 3
        assert all(0 <= pc <= 11 for pc in pitch_classes)
        assert pitch_classes == sorted(pitch_classes)

    @pytest.mark.parametrize("chord_a,chord_b,value", [(k[0], k[1], v) for k, v in OVERLAP_COUNTS.items()])
    def test_overlap_counts(self, chord_a, chord_b, value):
        inter = set(DIATONIC_CHORDS[chord_a]) & set(DIATONIC_CHORDS[chord_b])
        assert len(inter) == value

    @pytest.mark.parametrize("chord_a,chord_b,value", [(k[0], k[1], v) for k, v in DISTANCES.items()])
    def test_jaccard_distances(self, chord_a, chord_b, value):
        # Jaccard distance: 1 - |A ∩ B| / |A ∪ B|
        a_set = set(DIATONIC_CHORDS[chord_a])
        b_set = set(DIATONIC_CHORDS[chord_b])
        inter = len(a_set & b_set)
        union = len(a_set | b_set)
        expected_dist = 1.0 - inter / union
        assert abs(value - expected_dist) < 1e-9
