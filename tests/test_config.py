"""M0.T2: Config dataclass, YAML round-trip, validation, and 1D constraints."""
import tempfile
import importlib
import pytest
from tests.golden import (
    DIATONIC_CHORDS, OVERLAP_COUNTS, DISTANCES,
    WINDOW_TOTAL_SLOTS, WINDOW_SLOTS, WINDOW_OCCUPIED_INDICES, WINDOW_VACANT_INDICES
)


def _get_config_class():
    mod = importlib.import_module("schellingchords.config")
    return mod.Config


class TestConfigDefaults:
    def test_default_values(self):
        Config = _get_config_class()
        cfg = Config()
        assert cfg.bars_per_window == 4
        assert cfg.beats_per_bar == 4
        assert cfg.radius == 2
        assert cfg.happiness == 0.5
        assert cfg.vacancy_fraction == 0.25
        assert cfg.n_chord_types == 3
        assert cfg.tempo_bpm == 100
        assert cfg.metric == "pitch_class_overlap"
        assert cfg.vocabulary == "diatonic_major"

    def test_required_fields_exist(self):
        Config = _get_config_class()
        cfg = Config()
        required = {"n_chord_types", "bars_per_window", "vacancy_fraction",
                    "tolerance", "happiness", "radius", "tempo_bpm", "seed"}
        assert required.issubset(cfg.__dataclass_fields__.keys())

    def test_no_2d_fields(self):
        """M0: Config must NOT contain width/height/density/threshold/n_chords."""
        Config = _get_config_class()
        cfg = Config()
        forbidden = {"width", "height", "density", "threshold", "n_chords"}
        assert not forbidden.intersection(cfg.__dataclass_fields__.keys())


class TestConfigValidation:
    @pytest.mark.parametrize("vacancy, should_pass", [
        (0.0, True), (0.25, True), (0.99, True),
        (-0.1, False), (1.0, False), (1.5, False)
    ])
    def test_vacancy_fraction_bounds(self, vacancy, should_pass):
        Config = _get_config_class()
        if should_pass:
            Config(vacancy_fraction=vacancy)
        else:
            with pytest.raises(ValueError):
                Config(vacancy_fraction=vacancy)

    @pytest.mark.parametrize("n_types, should_pass", [
        (2, True), (3, True), (12, True),
        (1, False), (0, False), (-1, False)
    ])
    def test_n_chord_types_min(self, n_types, should_pass):
        Config = _get_config_class()
        if should_pass:
            Config(n_chord_types=n_types)
        else:
            with pytest.raises(ValueError):
                Config(n_chord_types=n_types)


class TestConfigYamlRoundTrip:
    def test_save_load_roundtrip(self):
        Config = _get_config_class()
        cfg = Config(seed=42, tolerance=0.75, radius=3)
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            cfg.save_yaml(f.name)
            loaded = Config.load_yaml(f.name)
        assert loaded.seed == cfg.seed
        assert loaded.tolerance == cfg.tolerance
        assert loaded.radius == cfg.radius
        assert loaded.bars_per_window == cfg.bars_per_window


class TestGoldenConsistency:
    def test_window_invariants(self):
        """1D window must satisfy total = occupied + vacant, flat list length matches."""
        assert len(WINDOW_SLOTS) == WINDOW_TOTAL_SLOTS
        assert len(WINDOW_OCCUPIED_INDICES) + len(WINDOW_VACANT_INDICES) == WINDOW_TOTAL_SLOTS
        assert sum(WINDOW_SLOTS) == len(WINDOW_OCCUPIED_INDICES)
        assert all(idx in range(WINDOW_TOTAL_SLOTS) for idx in WINDOW_OCCUPIED_INDICES)
        assert all(idx in range(WINDOW_TOTAL_SLOTS) for idx in WINDOW_VACANT_INDICES)

    @pytest.mark.parametrize("chord_name, pcs", DIATONIC_CHORDS.items())
    def test_chord_pitch_classes_sorted(self, chord_name, pcs):
        assert pcs == sorted(pcs)
        assert all(0 <= pc <= 11 for pc in pcs)

    @pytest.mark.parametrize("a, b, overlap", [(*k, v) for k, v in OVERLAP_COUNTS.items()])
    def test_overlap_counts_match_golden(self, a, b, overlap):
        assert len(set(DIATONIC_CHORDS[a]) & set(DIATONIC_CHORDS[b])) == overlap

    @pytest.mark.parametrize("a, b, dist", [(*k, v) for k, v in DISTANCES.items()])
    def test_jaccard_distance_golden(self, a, b, dist):
        """Jaccard distance: 1 - |a ∩ b| / |a ∪ b|, normalized to [0, 1]"""
        inter = len(set(DIATONIC_CHORDS[a]) & set(DIATONIC_CHORDS[b]))
        union = len(set(DIATONIC_CHORDS[a]) | set(DIATONIC_CHORDS[b]))
        assert abs(1.0 - inter / union - dist) < 1e-9
