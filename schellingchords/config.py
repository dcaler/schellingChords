from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import yaml


@dataclass(frozen=True)
class Config:
    bars_per_window: int = 4
    beats_per_bar: int = 4
    radius: int = 2
    tolerance: float = 0.5
    happiness: float = 0.5
    vacancy_fraction: float = 0.25
    n_chord_types: int = 3
    n_steps: int = 100
    seed: int = 42
    tempo_bpm: int = 100
    metric: str = "pitch_class_overlap"
    vocabulary: str = "diatonic_major"

    def __post_init__(self):
        if not (0 <= self.vacancy_fraction < 1):
            raise ValueError("vacancy_fraction must be in [0, 1)")
        if self.n_chord_types < 2:
            raise ValueError("n_chord_types must be >= 2")

    @classmethod
    def load_yaml(cls, path: str) -> "Config":
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def save_yaml(self, path: str) -> None:
        data = {
            "bars_per_window": self.bars_per_window,
            "beats_per_bar": self.beats_per_bar,
            "radius": self.radius,
            "tolerance": self.tolerance,
            "happiness": self.happiness,
            "vacancy_fraction": self.vacancy_fraction,
            "n_chord_types": self.n_chord_types,
            "n_steps": self.n_steps,
            "seed": self.seed,
            "tempo_bpm": self.tempo_bpm,
            "metric": self.metric,
            "vocabulary": self.vocabulary,
        }
        with open(path, "w") as f:
            yaml.dump(data, f)


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.

    Args:
        path: Path to the YAML configuration file. If None, returns default config.

    Returns:
        Dictionary containing configuration parameters.
    """
    if path is None:
        return {}
    cfg = Config.load_yaml(path)
    return {
        "bars_per_window": cfg.bars_per_window,
        "beats_per_bar": cfg.beats_per_bar,
        "radius": cfg.radius,
        "tolerance": cfg.tolerance,
        "happiness": cfg.happiness,
        "vacancy_fraction": cfg.vacancy_fraction,
        "n_chord_types": cfg.n_chord_types,
        "n_steps": cfg.n_steps,
        "seed": cfg.seed,
        "tempo_bpm": cfg.tempo_bpm,
        "metric": cfg.metric,
        "vocabulary": cfg.vocabulary,
    }


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate the configuration dictionary.

    Args:
        config: Configuration dictionary to validate.

    Returns:
        True if configuration is valid, False otherwise.
    """
    try:
        Config(**config)
        return True
    except (ValueError, TypeError):
        return False
