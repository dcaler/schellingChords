"""Gate test G1: From a Config, select_types(diatonic_major, n_chord_types) yields
n_chord_types distinct valid Chords with voicings consistent with their pitch classes.

Combines M0 (Config), M1.T1 (Chord type), and M1.T2 (vocabulary + select_types).
"""

import pytest
from tests.golden import DIATONIC_CHORDS


@pytest.fixture
def config_module():
    try:
        from schellingchords import config
        return config
    except ImportError:
        pytest.skip("schellingchords.config not yet implemented")


@pytest.fixture
def Config(config_module):
    return config_module.Config


@pytest.fixture
def vocab_module():
    try:
        from schellingchords import vocabulary
        return vocabulary
    except ImportError:
        pytest.skip("schellingchords.vocabulary not yet implemented")


@pytest.fixture
def diatonic_major(vocab_module):
    return vocab_module.diatonic_major


@pytest.fixture
def select_types(vocab_module):
    return vocab_module.select_types


class TestGateChords:
    """Integration gate: Config -> select_types -> valid Chords."""

    def test_gate_basic(self, Config, diatonic_major, select_types):
        """From a Config, select_types yields n_chord_types distinct valid Chords."""
        import random

        cfg = Config(
            n_chord_types=4,
            bars_per_window=4,
            vacancy_fraction=0.3,
            tolerance=0.5,
            happiness=0.5,
            radius=2,
            tempo_bpm=120,
            seed=42,
        )

        rng = random.Random(cfg.seed)
        chords = select_types(diatonic_major, n=cfg.n_chord_types, rng=rng)

        # Must return exactly n_chord_types chords
        assert len(chords) == cfg.n_chord_types

        # All must be distinct
        assert len(chords) == len(set(chords))

        # All must be valid Chord instances with correct structure
        for c in chords:
            # T1: Immutable attributes exist and have correct types
            assert hasattr(c, "name")
            assert hasattr(c, "root")
            assert hasattr(c, "quality")
            assert hasattr(c, "pitch_classes")
            assert hasattr(c, "midi_voicing")

            assert isinstance(c.pitch_classes, frozenset)
            assert isinstance(c.midi_voicing, tuple)

            # T1: pitch_classes are valid pitch classes (0-11)
            assert all(0 <= pc <= 11 for pc in c.pitch_classes)

            # T1: voicing reduces mod 12 to pitch_classes
            reduced = frozenset(midi % 12 for midi in c.midi_voicing)
            assert reduced == c.pitch_classes

            # T1: root is in pitch_classes
            assert c.root in c.pitch_classes

        # T2: All chords must come from diatonic_major vocabulary
        vocab_chords = diatonic_major()
        vocab_names = {c.name for c in vocab_chords}
        for c in chords:
            assert c.name in vocab_names

        # T2: Pitch classes must match golden values
        chord_by_name = {c.name: c for c in chords}
        for name, expected_pcs in DIATONIC_CHORDS.items():
            if name in chord_by_name:
                assert sorted(chord_by_name[name].pitch_classes) == expected_pcs

    def test_gate_max_types(self, Config, diatonic_major, select_types):
        """Gate with n_chord_types=7 (full vocabulary)."""
        import random

        cfg = Config(
            n_chord_types=7,
            bars_per_window=4,
            vacancy_fraction=0.25,
            tolerance=0.6,
            happiness=0.5,
            radius=3,
            tempo_bpm=100,
            seed=99,
        )

        rng = random.Random(cfg.seed)
        chords = select_types(diatonic_major, n=cfg.n_chord_types, rng=rng)

        assert len(chords) == 7
        assert len(set(chords)) == 7

        # All 7 diatonic triads must be present
        names = {c.name for c in chords}
        assert names == set(DIATONIC_CHORDS.keys())

    def test_gate_min_types(self, Config, diatonic_major, select_types):
        """Gate with n_chord_types=2 (minimum valid)."""
        import random

        cfg = Config(
            n_chord_types=2,
            bars_per_window=4,
            vacancy_fraction=0.4,
            tolerance=0.4,
            happiness=0.5,
            radius=1,
            tempo_bpm=140,
            seed=7,
        )

        rng = random.Random(cfg.seed)
        chords = select_types(diatonic_major, n=cfg.n_chord_types, rng=rng)

        assert len(chords) == 2
        assert len(set(chords)) == 2

        for c in chords:
            reduced = frozenset(midi % 12 for midi in c.midi_voicing)
            assert reduced == c.pitch_classes

    def test_config_fields_exist(self, Config):
        """Config must have exactly the specified fields."""
        cfg = Config(
            n_chord_types=4,
            bars_per_window=4,
            vacancy_fraction=0.3,
            tolerance=0.5,
            happiness=0.5,
            radius=2,
            tempo_bpm=120,
            seed=42,
        )
        assert cfg.n_chord_types == 4
        assert cfg.bars_per_window == 4
        assert cfg.vacancy_fraction == 0.3
        assert cfg.tolerance == 0.5
        assert cfg.happiness == 0.5
        assert cfg.radius == 2
        assert cfg.tempo_bpm == 120
        assert cfg.seed == 42

    def test_config_1d_window_consistency(self, Config):
        """Config bars_per_window must imply 1D slot count (bars*4)."""
        cfg = Config(
            n_chord_types=3,
            bars_per_window=4,
            vacancy_fraction=0.25,
            tolerance=0.5,
            happiness=0.5,
            radius=2,
            tempo_bpm=120,
            seed=0,
        )
        total_slots = cfg.bars_per_window * 4
        assert total_slots == 16
        assert cfg.vacancy_fraction >= 0.0
        assert cfg.vacancy_fraction <= 1.0
