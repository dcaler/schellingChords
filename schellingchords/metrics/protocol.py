"""
Protocol definition for distance metrics between chords.
"""
from typing import Protocol, Sequence
from typing_extensions import runtime_checkable


@runtime_checkable
class DistanceMetric(Protocol):
    """
    Protocol for calculating the distance between two chords.

    Methods:
        distance: Calculate the distance between two chords.
    """

    def distance(self, a: Sequence[int], b: Sequence[int]) -> float:
        """
        Calculate the distance between two chords.

        Args:
            a: The first chord, represented as a sequence of pitch classes.
            b: The second chord, represented as a sequence of pitch classes.

        Returns:
            The distance between the two chords.
        """
        ...
