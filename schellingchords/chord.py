"""Canonical ``schellingchords.chord`` module (M1.T1).

The immutable :class:`Chord` type is implemented in :mod:`schellingchords.chords`;
this module re-exports it under the singular name the frozen tests import
(``from schellingchords import chord``), keeping a single source of truth.
"""

from schellingchords.chords import Chord

__all__ = ["Chord"]
