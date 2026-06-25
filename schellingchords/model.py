import random
from typing import List, Optional
from mesa import Model

from schellingchords.config import Config
from schellingchords.runtime import RuntimeParams
from schellingchords.chords import VOCABULARIES, diatonic_major, select_types


class SchellingChordModel(Model):
    """Mesa agent-based model for Schelling segregation of chords."""

    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config
        self.params = RuntimeParams(
            tolerance=config.tolerance,
            happiness=config.happiness,
            vacancy_fraction=config.vacancy_fraction,
            radius=config.radius,
        )
        self.window_length = config.bars_per_window * config.beats_per_bar
        self.rng = random.Random(config.seed)

        n_vacant = round(config.vacancy_fraction * self.window_length)
        n_agents = self.window_length - n_vacant

        vocab = VOCABULARIES.get(config.vocabulary, diatonic_major)
        chord_types = select_types(vocab, config.n_chord_types, self.rng)

        base_count = n_agents // len(chord_types)
        remainder = n_agents % len(chord_types)
        chord_names = []
        for i, chord in enumerate(chord_types):
            count = base_count + (1 if i < remainder else 0)
            chord_names.extend([chord.name] * count)

        self.rng.shuffle(chord_names)

        self.window = [None] * self.window_length
        vacant_indices = set(self.rng.sample(range(self.window_length), n_vacant))
        occupied_indices = [i for i in range(self.window_length) if i not in vacant_indices]

        for idx, name in zip(occupied_indices, chord_names):
            self.window[idx] = name

    def step(self) -> None:
        tolerance = self.params.tolerance
        happiness = self.params.happiness
        _vacancy_fraction = self.params.vacancy_fraction
        radius = self.params.radius

        agents = [i for i, s in enumerate(self.window) if s is not None]
        vacant = [i for i, s in enumerate(self.window) if s is None]

        if not vacant:
            return

        unsatisfied = []
        for i in agents:
            start = max(0, i - radius)
            end = min(self.window_length, i + radius + 1)
            neighbors = [
                self.window[j]
                for j in range(start, end)
                if j != i and self.window[j] is not None
            ]

            if not neighbors:
                sat = 1.0
            else:
                same = sum(1 for n in neighbors if n == self.window[i])
                sat = same / len(neighbors)

            if sat < happiness:
                unsatisfied.append(i)

        if not unsatisfied:
            return

        self.rng.shuffle(vacant)
        moves = []
        for i in unsatisfied:
            if vacant:
                tgt = vacant.pop(0)
                moves.append((i, tgt))

        for src, tgt in moves:
            self.window[tgt] = self.window[src]
            self.window[src] = None

    def run(self, n_steps: int) -> List[List[Optional[str]]]:
        history = []
        for _ in range(n_steps):
            self.step()
            history.append(list(self.window))
        return history
