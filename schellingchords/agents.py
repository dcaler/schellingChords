from typing import Any, Callable, List, Optional
from mesa import Agent


class ChordAgent(Agent):
    """
    Agent representing a chord in the Schelling segregation model.

    Attributes:
        unique_id: Unique identifier for the agent.
        model: Reference to the model instance.
        chord_name: Name of the chord held by the agent.
        chord_type: Type of chord (e.g., major, minor).
    """

    def __init__(
        self,
        unique_id: int,
        model: Any = None,
        chord_type: str = "major",
    ) -> None:
        """
        Initialize the ChordAgent.

        Args:
            unique_id: Unique identifier for the agent.
            model: Reference to the model instance. May be ``None`` when the agent
                is constructed standalone for unittesting the pure satisfaction
                logic — in that case we skip Mesa's ``Agent.__init__`` (which would
                call ``model.register_agent(self)`` and crash on ``None``).
            chord_type: Type of chord.
        """
        if model is not None:
            super().__init__(model)
        self.unique_id = unique_id
        self.model = model
        self.chord_name: Optional[str] = None
        self.chord_type = chord_type

    def satisfaction(
        self, neighbors: List[str], metric: Callable, tolerance: float = None
    ) -> float:
        """
        Mean dissimilarity to occupied neighbours: the average distance from this
        chord to each occupied neighbour, normalised to [0, 1] by neighbour count.

        Lower is better (0 = every neighbour identical). Vacuously 0.0 when there
        are no occupied neighbours (nothing to be unlike). ``tolerance`` is accepted
        for signature compatibility and unused.

        Args:
            neighbors: List of chord names for occupied neighboring slots.
            metric: Callable that computes distance between two chord names.

        Returns:
            Mean neighbour distance in [0, 1].
        """
        if not neighbors:
            return 0.0
        return sum(metric(self.chord_name, n) for n in neighbors) / len(neighbors)

    def is_satisfied(
        self,
        neighbors: List[str],
        metric: Callable,
        tolerance: float,
    ) -> bool:
        """
        Satisfied iff the mean dissimilarity to occupied neighbours is within
        tolerance (``mean distance <= tolerance``). A chord with no occupied
        neighbours is vacuously satisfied.
        """
        return self.satisfaction(neighbors, metric) <= tolerance

    def step(self) -> None:
        """Execute one step of the agent's behavior."""
        pass

    def get_agent_data(self) -> dict:
        """Return agent-level data for reporting."""
        return {}

    def desired_slot(
        self,
        vacant_indices: List[int],
        slots: Any,
        metric: Callable,
        tolerance: float,
        rng: Any,
    ) -> int:
        """
        Choose the best-improving empty slot among the vacant indices.

        Evaluates satisfaction for each vacant slot, selects the one(s) that
        maximize satisfaction, and breaks ties deterministically using the
        provided RNG.

        Args:
            vacant_indices: List of indices representing empty slots.
            slots: Data structure where ``slots[idx]`` yields the list of
                   neighbor chord names for slot ``idx``.
            metric: Callable that computes distance between two chord names.
            tolerance: Maximum acceptable distance.
            rng: Random number generator for deterministic tie-breaking.

        Returns:
            The index of the slot that maximizes satisfaction.
        """
        best_diff = None
        best_candidates = []
        for idx in vacant_indices:
            neighbors = slots[idx]
            diff = self.satisfaction(neighbors, metric)   # mean dissimilarity; lower is better
            if best_diff is None or diff < best_diff:
                best_diff = diff
                best_candidates = [idx]
            elif diff == best_diff:
                best_candidates.append(idx)
        return rng.choice(best_candidates)
