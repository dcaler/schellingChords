"""Pitch class overlap metric based on Jaccard distance."""

from typing import Iterable


class PitchClassOverlap:
    """
    Jaccard distance metric on pitch class sets.
    
    Computes d(A, B) = 1 - |A ∩ B| / |A ∪ B|
    
    Properties:
        - d(x, x) = 0
        - d(a, b) = d(b, a)
        - d(a, b) >= 0
        - d(a, b) <= 1
    """
    
    def distance(self, a: Iterable[int], b: Iterable[int]) -> float:
        """
        Compute Jaccard distance between two pitch class sets.
        
        Args:
            a: First pitch class collection.
            b: Second pitch class collection.
            
        Returns:
            Jaccard distance between 0 and 1.
        """
        set_a = set(a)
        set_b = set(b)
        union = set_a | set_b
        if not union:
            return 0.0
        intersection = set_a & set_b
        return 1.0 - len(intersection) / len(union)
