"""Runtime visualization — lattice strip + playhead."""

import math
import pygame
from typing import Dict, List, Optional, Tuple

# Compatibility shim for pygame 2.x where pixels_rgb was removed in favor of pixels3d
if not hasattr(pygame.surfarray, 'pixels_rgb'):
    pygame.surfarray.pixels_rgb = pygame.surfarray.pixels3d


class LatticeView:
    """Renders the current window as a strip of beat-cells colored by chord type.

    Each cell corresponds to a beat slot in the window. Occupied slots are colored
    by chord type using a stable palette; empty slots (rests) use a neutral colour.
    A playhead indicator marks the active beat position.
    """

    def __init__(
        self,
        n_chord_types: int = 7,
        width: int = 800,
        height: int = 200,
        n_cells: int = 16,
    ) -> None:
        self.width = width
        self.height = height
        self.n_cells = n_cells
        self.cell_width = width // n_cells
        self.cell_height = height

        self.surface = pygame.Surface((width, height))

        self.palette = self._generate_palette(n_chord_types)
        self.rest_colour: Tuple[int, int, int] = (30, 30, 30)

        self.playhead: int = 0
        self.window_slots: List[Optional[int]] = [None] * n_cells
        self.window_index: int = 0

    @staticmethod
    def _generate_palette(n: int) -> Dict[int, Tuple[int, int, int]]:
        """Generate a stable palette of n distinct colours keyed by chord type index."""
        palette: Dict[int, Tuple[int, int, int]] = {}
        for i in range(n):
            hue = i * 360 / n
            r = int(128 + 127 * math.sin(2 * math.pi * hue / 360))
            g = int(128 + 127 * math.sin(2 * math.pi * (hue + 120) / 360))
            b = int(128 + 127 * math.sin(2 * math.pi * (hue + 240) / 360))
            palette[i] = (
                max(0, min(255, r)),
                max(0, min(255, g)),
                max(0, min(255, b)),
            )
        return palette

    def render(self, surface: pygame.Surface) -> None:
        """Draw the lattice strip onto the given pygame Surface."""
        # Fill background with rest colour to ensure non-blank surface
        surface.fill(self.rest_colour)

        # Draw each cell
        for idx, slot in enumerate(self.window_slots):
            x = idx * self.cell_width
            # Treat None, 0, negative, or out-of-range values as rests
            if slot is not None and slot > 0 and slot in self.palette:
                colour = self.palette[slot]
            else:
                colour = self.rest_colour
            pygame.draw.rect(
                surface,
                colour,
                (x, 0, self.cell_width, self.cell_height),
            )

        # Draw playhead indicator (wrap to valid range for drawing)
        ph = self.playhead % self.n_cells
        pygame.draw.line(
            surface,
            (200, 20, 40),
            (ph * self.cell_width, 0),
            (ph * self.cell_width, self.height),
            width=4,
        )
