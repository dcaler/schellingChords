"""Frozen tests for M1.T1: Immutable Chord type.

Tests assert concrete golden pitch-class sets, voicing consistency,
immutability, and equality/hash semantics.
"""

import pytest
from tests.golden import DIATONIC_CHORDS

# Expected octave-4 voicings (MIDI) for each diatonic triad
EXPECTED_VOICINGS: dict[str, tuple[int, ...]] = {
    "I": (60, 64, 67),      # C4 E4 G4
    "ii": (62, 65, 69),     # D4 F4 A4
    "iii": (64, 67, 71),    # E4 G4 B4
    "IV": (65, 69, 72),     # F4 A4 C5
    "V": (67, 71, 74),      # G4 B4 D5
    "vi": (69, 72, 76),     # A4 C5 E5
    "vii°": (71, 74, 77),   # B4 D5 F5
}


@pytest.fixture
def chord_module():
    """Import chord module; skip if not yet implemented."""
    try:
        from schellingchords import chord
        return chord
    except ImportError:
        pytest.skip("schellingchords.chord not yet implemented")


@pytest.fixture
def Chord(chord_module):
    return chord_module.Chord


class TestChordImmutability:
    """Chord instances must be immutable after construction."""

    def test_cannot_modify_name(self, Chord):
        c = Chord(name="I", root=0, quality="major", pitch_classes=frozenset([0, 4, 7]), midi_voicing=(60, 64, 67))
        with pytest.raises(AttributeError):
            c.name = "IV"

    def test_cannot_modify_root(self, Chord):
        c = Chord(name="I", root=0, quality="major", pitch_classes=frozenset([0, 4, 7]), midi_voicing=(60, 64, 67))
        with pytest.raises(AttributeError):
            c.root = 5

    def test_cannot_modify_quality(self, Chord):
        c = Chord(name="I", root=0, quality="major", pitch_classes=frozenset([0, 4, 7]), midi_voicing=(60, 64, 67))
        with pytest.raises(AttributeError):
            c.quality = "minor"

    def test_cannot_modify_pitch_classes(self, Chord):
        c = Chord(name="I", root=0, quality="major", pitch_classes=frozenset([0, 4, 7]), midi_voicing=(60, 64, 67))
        with pytest.raises(AttributeError):
            c.pitch_classes = frozenset([0, 5, 9])

    def test_cannot_modify_midi_voicing(self, Chord):
        c = Chord(name="I", root=0, quality="major", pitch_classes=frozenset([0, 4, 7]), midi_voicing=(60, 64, 67))
        with pytest.raises(AttributeError):
            c.midi_voicing = (60, 64, 68)

    def test_pitch_classes_is_frozenset(self, Chord):
        c = Chord(name="I", root=0, quality="major", pitch_classes=frozenset([0, 4, 7]), midi_voicing=(60, 64, 67))
        assert isinstance(c.pitch_classes, frozenset)

    def test_midi_voicing_is_tuple(self, Chord):
        c = Chord(name="I", root=0, quality="major", pitch_classes=frozenset([0, 4, 7]), midi_voicing=(60, 64, 67))
        assert isinstance(c.midi_voicing, tuple)


class TestChordEqualityAndHash:
    """Equality and hash must be based on content, not identity."""

    def test_equal_content_same_hash(self, Chord):
        c1 = Chord(name="I", root=0, quality="major", pitch_classes=frozenset([0, 4, 7]), midi_voicing=(60, 64, 67))
        c2 = Chord(name="I", root=0, quality="major", pitch_classes=frozenset([0, 4, 7]), midi_voicing=(60, 64, 67))
        assert c1 == c2
        assert hash(c1) == hash(c2)

    def test_different_pitch_classes_unequal(self, Chord):
        c1 = Chord(name="I", root=0, quality="major", pitch_classes=frozenset([0, 4, 7]), midi_voicing=(60, 64, 67))
        c2 = Chord(name="IV", root=5, quality="major", pitch_classes=frozenset([0, 5, 9]), midi_voicing=(65, 69, 72))
        assert c1 != c2

    def test_different_voicing_unequal(self, Chord):
        c1 = Chord(name="I", root=0, quality="major", pitch_classes=frozenset([0, 4, 7]), midi_voicing=(60, 64, 67))
        c2 = Chord(name="I", root=0, quality="major", pitch_classes=frozenset([0, 4, 7]), midi_voicing=(72, 76, 79))
        assert c1 != c2

    def test_usable_in_set(self, Chord):
        c1 = Chord(name="I", root=0, quality="major", pitch_classes=frozenset([0, 4, 7]), midi_voicing=(60, 64, 67))
        c2 = Chord(name="I", root=0, quality="major", pitch_classes=frozenset([0, 4, 7]), midi_voicing=(60, 64, 67))
        s = {c1, c2}
        assert len(s) == 1

    def test_usable_as_dict_key(self, Chord):
        c1 = Chord(name="I", root=0, quality="major", pitch_classes=frozenset([0, 4, 7]), midi_voicing=(60, 64, 67))
        d = {c1: "tonic"}
        c2 = Chord(name="I", root=0, quality="major", pitch_classes=frozenset([0, 4, 7]), midi_voicing=(60, 64, 67))
        assert d[c2] == "tonic"


class TestChordVoicingConsistency:
    """Voicing MIDI notes must reduce mod 12 to the pitch_classes set."""

    @pytest.mark.parametrize("name,pitch_classes,voicing", [
        ("I", frozenset([0, 4, 7]), (60, 64, 67)),
        ("ii", frozenset([2, 5, 9]), (62, 65, 69)),
        ("iii", frozenset([4, 7, 11]), (64, 67, 71)),
        ("IV", frozenset([0, 5, 9]), (65, 69, 72)),
        ("V", frozenset([2, 7, 11]), (67, 71, 74)),
        ("vi", frozenset([0, 4, 9]), (69, 72, 76)),
        ("vii°", frozenset([2, 5, 11]), (71, 74, 77)),
    ])
    def test_voicing_reduces_to_pitch_classes(self, Chord, name, pitch_classes, voicing):
        c = Chord(name=name, root=voicing[0] % 12, quality="major" if name in ("I", "IV", "V") else ("minor" if name in ("ii", "iii", "vi") else "diminished"),
                  pitch_classes=pitch_classes, midi_voicing=voicing)
        reduced = frozenset(midi % 12 for midi in c.midi_voicing)
        assert reduced == c.pitch_classes

    def test_voicing_length_matches_pitch_classes(self, Chord):
        c = Chord(name="I", root=0, quality="major", pitch_classes=frozenset([0, 4, 7]), midi_voicing=(60, 64, 67))
        assert len(c.midi_voicing) == len(c.pitch_classes)


class TestChordGoldenInstances:
    """Concrete golden Chord instances for all 7 diatonic triads."""

    @pytest.mark.parametrize("name,root,quality,pitch_classes,voicing", [
        ("I", 0, "major", frozenset([0, 4, 7]), (60, 64, 67)),
        ("ii", 2, "minor", frozenset([2, 5, 9]), (62, 65, 69)),
        ("iii", 4, "minor", frozenset([4, 7, 11]), (64, 67, 71)),
        ("IV", 5, "major", frozenset([0, 5, 9]), (65, 69, 72)),
        ("V", 7, "major", frozenset([2, 7, 11]), (67, 71, 74)),
        ("vi", 9, "minor", frozenset([0, 4, 9]), (69, 72, 76)),
        ("vii°", 11, "diminished", frozenset([2, 5, 11]), (71, 74, 77)),
    ])
    def test_golden_chord_attributes(self, Chord, name, root, quality, pitch_classes, voicing):
        c = Chord(name=name, root=root, quality=quality, pitch_classes=pitch_classes, midi_voicing=voicing)
        assert c.name == name
        assert c.root == root
        assert c.quality == quality
        assert c.pitch_classes == pitch_classes
        assert c.midi_voicing == voicing
        assert 0 <= c.root <= 11
        assert all(0 <= pc <= 11 for pc in c.pitch_classes)
        assert all(midi >= 60 for midi in c.midi_voicing)  # octave 4+
