from typing import FrozenSet, Tuple

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
        self._midi_voicing = tuple(midi % 12 for midi in midi_voicing)

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
