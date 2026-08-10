from typing import Any, Dict, FrozenSet, List, Tuple

class Chord:
    def __init__(
        self,
        name: str,
        root: int,
        quality: str,
        pitch_classes: FrozenSet[int],
        midi_voicing: Tuple[int, ...]
    ) -> None:
        if not (0 <= root <= 11):
            raise ValueError("root must be in [0, 11]")
        if not all(0 <= pc <= 11 for pc in pitch_classes):
            raise ValueError("pitch_classes must contain only integers in [0, 11]")
        if len(midi_voicing) != len(pitch_classes):
            raise ValueError("midi_voicing length does not match pitch_classes")
        self._name = name
        self._root = root
        self._quality = quality
        self._pitch_classes = pitch_classes
        # Preserve the actual MIDI note numbers (octave 4+); the mod-12 reduction
        # is the *pitch_classes* set, kept separately. Reducing here would destroy
        # octave information and collapse distinct voicings.
        self._midi_voicing = tuple(midi_voicing)

    @property
    def name(self) -> str:
        return self._name

    @property
    def root(self) -> int:
        return self._root

    @property
    def quality(self) -> str:
        return self._quality

    @property
    def pitch_classes(self) -> FrozenSet[int]:
        return self._pitch_classes

    @property
    def midi_voicing(self) -> Tuple[int, ...]:
        return self._midi_voicing

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Chord):
            return False
        return (
            self.name == other.name and
            self.root == other.root and
            self.quality == other.quality and
            self.pitch_classes == other.pitch_classes and
            self.midi_voicing == other.midi_voicing
        )

    def __hash__(self) -> int:
        return hash((self.name, self.root, self.quality, self.pitch_classes, self.midi_voicing))

    def __repr__(self) -> str:
        return f"Chord(name='{self.name}', root={self.root}, quality='{self.quality}', pitch_classes={self.pitch_classes!r}, midi_voicing={self.midi_voicing!r})"


def diatonic_major() -> List[Chord]:
    chords = [
        Chord("C", 0, "major", frozenset([0, 4, 7]), (60, 64, 67)),
        Chord("Dm", 2, "minor", frozenset([2, 5, 9]), (62, 65, 69)),
        Chord("Em", 4, "minor", frozenset([4, 7, 11]), (64, 67, 71)),
        Chord("F", 0, "major", frozenset([0, 5, 9]), (60, 65, 69)),
        Chord("G", 2, "major", frozenset([2, 7, 11]), (62, 67, 71)),
        Chord("Am", 0, "minor", frozenset([0, 4, 9]), (60, 64, 69)),
        Chord("Bdim", 2, "diminished", frozenset([2, 5, 11]), (62, 65, 71))
    ]
    return chords


def c_minor() -> List[Chord]:
    """C (harmonic/natural) minor triads: i, ii°, III, iv, V, VI, vii°.

    Holds the pitch content of the opening of Beethoven's 5th: the tonic gesture
    G-G-G-E♭ lives in ``Cm`` ({G,E♭} ⊂ {C,E♭,G}) and the dominant gesture
    F-F-F-D in ``Bdim`` ({F,D} ⊂ {B,D,F}). ``G`` and ``Bdim`` are defined
    identically to their ``diatonic_major`` entries (same name → same pitch
    classes), so the name→pitch-class lookups shared across vocabularies stay
    consistent. Scale-degree order (i, ii°, III, iv, V, VI, vii°) mirrors
    ``diatonic_major``.
    """
    return [
        Chord("Cm",   0, "minor",      frozenset([0, 3, 7]),  (60, 63, 67)),
        Chord("Ddim", 2, "diminished", frozenset([2, 5, 8]),  (62, 65, 68)),
        Chord("Eb",   3, "major",      frozenset([3, 7, 10]), (63, 67, 70)),
        Chord("Fm",   5, "minor",      frozenset([5, 8, 0]),  (65, 68, 72)),
        Chord("G",    2, "major",      frozenset([2, 7, 11]), (62, 67, 71)),
        Chord("Ab",   8, "major",      frozenset([8, 0, 3]),  (68, 72, 75)),
        Chord("Bdim", 2, "diminished", frozenset([2, 5, 11]), (62, 65, 71)),
    ]


# Registry of named vocabularies, keyed by name -> factory callable.
VOCABULARIES: Dict[str, Any] = {
    "diatonic_major": diatonic_major,
    "c_minor": c_minor,
}


def select_types(vocabulary: Any, n: int, rng: Any = None) -> List[Chord]:
    """Select ``n`` chords spread as far apart as possible in pitch-class space.

    Deterministic **dispersion / farthest-first** ordering: anchor on the
    vocabulary's first chord (the tonic), then repeatedly add the chord whose
    *minimum* Jaccard distance to those already chosen is largest, breaking ties
    by vocabulary order. This maximises harmonic spread (and, since the metric is
    coarse, coverage too), and is nested in ``n`` — raising ``n`` keeps the
    existing chords and adds one. For ``diatonic_major`` this yields
    ``C, Dm, G, Em, F, Am, Bdim``.

    ``vocabulary`` may be a factory callable (e.g. ``diatonic_major``) or an
    iterable of chords; ``n`` must be in ``[2, len(vocabulary)]``. ``rng`` is
    accepted for API compatibility and unused — selection no longer depends on the
    seed (the seed still governs spatial placement in the model).
    """
    chords = list(vocabulary()) if callable(vocabulary) else list(vocabulary)
    if not (2 <= n <= len(chords)):
        raise ValueError(f"n must be in [2, {len(chords)}]")

    def jaccard(a: Chord, b: Chord) -> float:
        union = len(a.pitch_classes | b.pitch_classes)
        return 1.0 - len(a.pitch_classes & b.pitch_classes) / union if union else 0.0

    chosen = [chords[0]]
    remaining = chords[1:]
    while remaining:
        # farthest-first: maximise the minimum distance to the chosen set; max()
        # returns the first (lowest vocab-order) candidate on ties.
        best = max(remaining, key=lambda c: min(jaccard(c, s) for s in chosen))
        chosen.append(best)
        remaining.remove(best)
    return chosen[:n]
