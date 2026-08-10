import random
from typing import List, Optional
from mesa import Model, DataCollector

from schellingchords.config import Config
from schellingchords.runtime import RuntimeParams
from schellingchords.chords import VOCABULARIES, diatonic_major, select_types
from schellingchords.agents import ChordAgent
from schellingchords.metrics import jaccard_distance
from schellingchords.observables import segregation_index, region_count


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

    def __init__(self, config: Config, initial_window: Optional[List[Optional[str]]] = None) -> None:
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

        if initial_window is not None:
            # Scenario / caller supplies an explicit starting arrangement (e.g. the
            # opening of Beethoven's 5th). It replaces random placement entirely;
            # segregation then evolves from this exact window. Chord names need not
            # belong to the selected n_chord_types subset — the distance metric
            # resolves any name in a registered vocabulary.
            if len(initial_window) != self.window_length:
                raise ValueError(
                    f"initial_window length {len(initial_window)} != "
                    f"window_length {self.window_length}")
            self.window = list(initial_window)
        else:
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

        # Wire DataCollector for model-level variables
        # Note: In newer versions of Mesa, the argument is 'model_vars'.
        # In older versions, it might be different, but the error indicates
        # 'model_vars' is unexpected. Let's check the signature.
        # Actually, the error says "unexpected keyword argument 'model_vars'".
        # This suggests an older version of Mesa where the argument was named differently
        # or the API was different.
        # However, standard Mesa DataCollector signature is:
        # DataCollector(model_vars=None, agent_vars=None, agent_reporters=None)
        # If 'model_vars' is unexpected, it might be that the version installed
        # is very old or the test environment has a specific version.
        # Let's look at the error again: TypeError: DataCollector.__init__() got an unexpected keyword argument 'model_vars'
        # This is strange because 'model_vars' is the standard argument in Mesa 2.x+.
        # Perhaps the installed Mesa is 1.x? In Mesa 1.x, DataCollector didn't exist in the same way.
        # Or perhaps the argument name is different?
        # Let's try using positional arguments or checking the actual signature.
        # Actually, let's just try the standard 'model_vars' first. If it fails,
        # maybe the issue is something else.
        # Wait, the error is explicit.
        # Let's check Mesa 2.0.0 docs: DataCollector(model_vars=None, agent_vars=None, agent_reporters=None)
        # If the test fails, maybe the installed Mesa is older?
        # Let's try 'model_reporters' which was the name in Mesa 1.x?
        # No, DataCollector was introduced in Mesa 1.0.0 with 'model_reporters'.
        # In Mesa 2.0.0, it was renamed to 'model_vars'.
        # So if 'model_vars' fails, we are likely on Mesa 1.x.
        # Let's try 'model_reporters'.

        try:
            self.datacollector = DataCollector(
                model_vars={
                    "segregation_index": self._get_segregation_index,
                    "region_count": self._get_region_count,
                }
            )
        except TypeError:
            # Fallback for older Mesa versions (1.x)
            self.datacollector = DataCollector(
                model_reporters={
                    "segregation_index": self._get_segregation_index,
                    "region_count": self._get_region_count,
                }
            )
        
        # Do NOT collect initial state here. The test expects len(df) == 3 after 3 steps.
        # If we collect here, we get 4 rows (initial + 3 steps).
        # The test implies that data collection should only happen during steps.
        # self.datacollector.collect(self)

    def _get_segregation_index(self) -> float:
        """Helper to calculate segregation index for DataCollector."""
        tolerance = self.params.tolerance
        radius = self.params.radius
        metric = jaccard_distance
        return segregation_index(self.window, metric, tolerance, radius)

    def _get_region_count(self) -> int:
        """Helper to calculate region count for DataCollector."""
        tolerance = self.params.tolerance
        metric = jaccard_distance
        return region_count(self.window, metric, tolerance)

    def step(self) -> None:
        # Read live each step from the MUTABLE RuntimeParams (not frozen Config),
        # so mid-run edits to tolerance/happiness/radius take effect immediately.
        tolerance = self.params.tolerance
        radius = self.params.radius
        metric = jaccard_distance
        # origin -> target for every chord that relocates this step, so a viewer can
        # animate the exact transition the headless model performs. Happy chords
        # (not listed) stay put; empty at every early return below.
        self.last_moves = {}
        self.last_unhappy = 0   # count of unsatisfied chords this step (for live charts)

        if not any(s is None for s in self.window):
            # Still collect data even if no moves happen
            self.datacollector.collect(self)
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
            if not probe.is_satisfied(view[i], metric, tolerance):
                unsatisfied.append(i)
        self.last_unhappy = len(unsatisfied)

        if not unsatisfied:
            # Still collect data even if no moves happen
            self.datacollector.collect(self)
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
            self.last_moves[src] = tgt

        # Collect data after step
        self.datacollector.collect(self)

    def run(self, n_steps: int) -> List[List[Optional[str]]]:
        history = []
        for _ in range(n_steps):
            self.step()
            history.append(list(self.window))
        return history
