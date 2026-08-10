"""DistanceMetric protocol + registry (canonical module).

The implementation lives in the ``schellingchords.metrics`` package; this module
re-exports the canonical symbols so the canonical import path
``from schellingchords.distance import get_metric`` yields the *same* registry
instance and semantics (returns an instance; raises ``KeyError`` on an unknown
name) as ``schellingchords.metrics.registry`` — rather than a divergent copy.
"""

from schellingchords.metrics.protocol import DistanceMetric
from schellingchords.metrics.pitch_class_overlap import PitchClassOverlap
from schellingchords.metrics.registry import METRICS, get_metric

__all__ = ["DistanceMetric", "PitchClassOverlap", "METRICS", "get_metric"]
