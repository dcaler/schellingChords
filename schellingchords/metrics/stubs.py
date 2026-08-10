"""
Stub implementations for distance metrics.
"""
from typing import Sequence


class TymoczkoVoiceLeading:
    """
    Stub implementation for Tymoczko voice leading distance metric.
    """

    def distance(self, a: Sequence[int], b: Sequence[int]) -> float:
        """
        Calculate the distance between two chords using Tymoczko voice leading.

        Args:
            a: The first chord, represented as a sequence of pitch classes.
            b: The second chord, represented as a sequence of pitch classes.

        Returns:
            The distance between the two chords.

        Raises:
            NotImplementedError: This method is not implemented yet.
        """
        raise NotImplementedError("TymoczkoVoiceLeading distance metric is not implemented yet.")


class TIV:
    """
    Stub implementation for TIV distance metric.
    """

    def distance(self, a: Sequence[int], b: Sequence[int]) -> float:
        """
        Calculate the distance between two chords using TIV.

        Args:
            a: The first chord, represented as a sequence of pitch classes.
            b: The second chord, represented as a sequence of pitch classes.

        Returns:
            The distance between the two chords.

        Raises:
            NotImplementedError: This method is not implemented yet.
        """
        raise NotImplementedError("TIV distance metric is not implemented yet.")
