"""LivePlayer: Real-time step+sonify clock for SchellingChords."""

import pygame
from typing import Optional, List, Dict, Any

from schellingchords.runtime import RuntimeParams


class LivePlayer:
    """Drives the model in real musical time, emitting ticks and triggering model steps."""

    def __init__(self, model: Any, runtime_params: Optional[RuntimeParams] = None) -> None:
        self.model = model
        if runtime_params is None:
            runtime_params = RuntimeParams()
            runtime_params.tolerance = 0.5
            runtime_params.happiness = 0.6
            runtime_params.vacancy_fraction = 0.25
            runtime_params.tempo_bpm = 120
        self.runtime_params = runtime_params
        self.playhead = 0
        self.window_index = 0
        self.paused = True
        self.playing = False
        self._current_window = self._extract_window()

    def _extract_window(self) -> List[Optional[str]]:
        """Extract the current window state from the model."""
        if hasattr(self.model, "window"):
            w = self.model.window
            if isinstance(w, (list, tuple)):
                return list(w)
        if hasattr(self.model, "grid"):
            try:
                return [cell[0] if cell else None for cell in self.model.grid]
            except Exception:
                pass
        return [None] * 16

    def generate_tick(self) -> Dict[str, Any]:
        """Generate a single tick dict, advancing playhead and triggering step at window end."""
        if self.paused:
            return {
                "window": self.window_index,
                "beat_index": self.playhead,
                "chord_or_rest": None,
            }

        window_size = len(self._current_window) if self._current_window else 16
        current_chord = self._current_window[self.playhead % window_size] if window_size > 0 else None
        if current_chord == 0:
            current_chord = None

        tick = {
            "window": self.window_index,
            "beat_index": self.playhead,
            "chord_or_rest": current_chord,
        }

        self.playhead += 1

        if window_size > 0 and self.playhead % window_size == 0:
            self.model.step()
            self._current_window = self._extract_window()
            self.window_index += 1

        return tick

    def play(self) -> None:
        """Start playback."""
        self.playing = True
        self.paused = False

    def pause(self) -> None:
        """Pause playback."""
        self.paused = True
        self.playing = False

    def step(self) -> None:
        """Manually advance one beat."""
        self.playhead += 1
        window_size = len(self._current_window) if self._current_window else 16
        if window_size > 0 and self.playhead % window_size == 0:
            self.model.step()
            self._current_window = self._extract_window()
            self.window_index += 1

    def reset(self) -> None:
        """Reset playhead, window index, and pause state."""
        self.playhead = 0
        self.window_index = 0
        self.paused = True
        self.playing = False
        self._current_window = self._extract_window()
