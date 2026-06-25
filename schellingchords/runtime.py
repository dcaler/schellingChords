from dataclasses import dataclass


@dataclass
class RuntimeParams:
    """Mutable runtime parameters for the SchellingChordModel."""
    tolerance: float = 0.5
    happiness: float = 0.5
    vacancy_fraction: float = 0.25
    radius: int = 2
