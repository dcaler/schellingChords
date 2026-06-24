"""
Registry for distance metrics.
"""
from typing import Dict

from schellingchords.metrics.protocol import DistanceMetric
from schellingchords.metrics.pitch_class_overlap import PitchClassOverlap


# Registry of available metrics
METRICS: Dict[str, DistanceMetric] = {
    "pitch_class_overlap": PitchClassOverlap(),
}


def get_metric(name: str) -> DistanceMetric:
    """
    Retrieve a distance metric by name.

    Args:
        name: The name of the metric.

    Returns:
        The distance metric instance.

    Raises:
        KeyError: If the metric is not found.
    """
    if name not in METRICS:
        raise KeyError(f"Metric '{name}' not found in registry.")
    return METRICS[name]
