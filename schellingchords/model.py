import random
from typing import List, Optional
from mesa import Model

from schellingchords.config import Config
from schellingchords.runtime import RuntimeParams
from schellingchords.chords import VOCABULARIES, diatonic_major, select_types
from schellingchords.agents import ChordAgent
from schellingchords.metrics import jaccard_distance


class _NeighborView:
    """Adapter exposing ``view[idx] -> [occupied neighbour names]`` for a window.

    ``ChordAgent.desired_slot`` consumes a ``slots`` object via ``slots[idx]``;
    this returns the occupied (non-``None``) chord names within ``radius`` of
    ``idx``, excluding ``idx`` itself. It reads the underlying window list live,
    so in-place relocations are reflected without rebuilding the view.
    """

    def __init__(self, window: List[Optional[str]], radius: int) -> None:
        self._window = window
        self._radius = radius

    def __getitem__(self, idx: int) -> List[str]:
        start = max(0, idx - self._radius)
        end = min(len(self._window), idx + self._radius + 1)
        return [
            self._window[j]
            for j in range(start, end)
            if j != idx and self._window[j] is not None
        ]


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
        # Read live each step from the MUTABLE RuntimeParams (not frozen Config),
        # so mid-run edits to tolerance/happiness/radius take effect immediately.
        tolerance = self.params.tolerance
        happiness = self.params.happiness
        radius = self.params.radius
        metric = jaccard_distance

        if not any(s is None for s in self.window):
            return

        # One throwaway agent reused as a probe so satisfaction / relocation use
        # the canonical, verified ChordAgent logic (distance metric + tolerance),
        # rather than a re-implemented identity rule. model=None => standalone path.
        probe = ChordAgent(unique_id=-1, model=None)
        view = _NeighborView(self.window, radius)

        occupied = [i for i, s in enumerate(self.window) if s is not None]
        unsatisfied = []
        for i in occupied:
            probe.chord_name = self.window[i]
            if not probe.is_satisfied(view[i], metric, tolerance, happiness):
                unsatisfied.append(i)

        if not unsatisfied:
            return

        # Faithful Schelling relocation: each unsatisfied agent moves to a
        # UNIFORMLY RANDOM vacant slot, not a best-improving one. A move may land
        # the agent somewhere it is still unsatisfied; segregation emerges only
        # from iterating this random search over many steps. (Whether a slot is
        # satisfying is still judged by the distance metric + tolerance above;
        # only the choice of target is random.) Agent order is shuffled so no
        # slot gets a positional pick advantage. Each move conserves the chord
        # multiset and the vacancy count: the target is currently empty and the
        # vacated source replaces it in the pool for later movers.
        self.rng.shuffle(unsatisfied)
        for src in unsatisfied:
            vacant = [j for j, s in enumerate(self.window) if s is None]
            tgt = self.rng.choice(vacant)
            self.window[tgt] = self.window[src]
            self.window[src] = None

    def run(self, n_steps: int) -> List[List[Optional[str]]]:
        history = []
        for _ in range(n_steps):
            self.step()
            history.append(list(self.window))
        return history
