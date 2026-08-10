"""Canonical ``schellingchords.vocabulary`` module (M1.T2).

Diatonic vocabulary, the ``VOCABULARIES`` registry, and ``select_types`` are
implemented in :mod:`schellingchords.chords`; this module re-exports them under
the name the frozen tests import (``from schellingchords import vocabulary``),
keeping a single source of truth.
"""

from schellingchords.chords import VOCABULARIES, diatonic_major, select_types

__all__ = ["diatonic_major", "VOCABULARIES", "select_types"]
