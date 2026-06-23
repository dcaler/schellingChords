"""Distance metrics registry for SchellingChords."""

from schellingchords.metrics.pitch_class_overlap import PitchClassOverlap

METRICS = {
    "pitch_class_overlap": PitchClassOverlap,
}


def get_metric(name: str) -> type:
    """Get a metric class by name."""
    if name not in METRICS:
        raise ValueError(f"Unknown metric: {name}")
    return METRICS[name]
