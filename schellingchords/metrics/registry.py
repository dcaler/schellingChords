"""
Registry for distance metrics.
"""
from typing import Dict, Type

from schellingchords.metrics.protocol import DistanceMetric


class PitchClassOverlap:
    """
    A simple distance metric based on pitch class overlap.
    """

    def distance(self, a: list[int], b: list[int]) -> float:
        """
        Calculate the distance between two chords based on pitch class overlap.

        Args:
            a: The first chord, represented as a list of pitch classes.
            b: The second chord, represented as a list of pitch classes.

        Returns:
            The distance between the two chords.
        """
        set_a = set(a)
        set_b = set(b)
        union = set_a.union(set_b)
        if not union:
            return 0.0
        intersection = set_a.intersection(set_b)
        return 1.0 - (len(intersection) / len(union))


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
