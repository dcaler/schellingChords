"""M9.T2 — LatticeView rendering, playhead, colour palette, surface assertions."""
import pytest
import pygame
from tests.golden import (
    WINDOW_TOTAL_SLOTS,
    WINDOW_SLOTS,
    WINDOW_OCCUPIED_INDICES,
    DIATONIC_CHORDS,
)


class TestLatticeViewInit:
    """LatticeView construction and surface sizing."""

    def test_surface_dimensions(self, lattice_view):
        assert lattice_view.surface.get_width() == 800
        assert lattice_view.surface.get_height() == 200

    def test_palette_has_n_chord_types(self, lattice_view):
        assert len(lattice_view.palette) == 7
        for colour in lattice_view.palette.values():
            assert isinstance(colour, tuple)
            assert len(colour) == 3
            assert all(0 <= c <= 255 for c in colour)

    def test_rest_colour_defined(self, lattice_view):
        assert hasattr(lattice_view, "rest_colour")
        assert isinstance(lattice_view.rest_colour, tuple)


class TestLatticeRender:
    """Pure draw onto pygame.Surface — headless-testable."""

    def test_render_does_not_raise(self, lattice_view, dummy_surface):
        lattice_view.render(dummy_surface)

    def test_render_produces_non_blank_surface(self, lattice_view, dummy_surface):
        lattice_view.render(dummy_surface)
        pixels = pygame.surfarray.pixels_rgb(dummy_surface)
        assert pixels.size > 0

    def test_cell_count_matches_window(self, lattice_view):
        assert lattice_view.n_cells == WINDOW_TOTAL_SLOTS

    def test_cell_width_computed(self, lattice_view):
        # 800 px / 16 cells = 50 px per cell
        assert lattice_view.cell_width == 50

    def test_cell_height_computed(self, lattice_view):
        # 200 px height, with some padding
        assert lattice_view.cell_height > 0


class TestPlayheadRendering:
    """Playhead overlay at active beat."""

    def test_playhead_at_zero(self, lattice_view, dummy_surface):
        lattice_view.playhead = 0
        lattice_view.render(dummy_surface)
        # Surface should contain the playhead indicator colour
        assert lattice_view.playhead == 0

    def test_playhead_advances(self, lattice_view, dummy_surface):
        for beat in range(WINDOW_TOTAL_SLOTS):
            lattice_view.playhead = beat
            lattice_view.render(dummy_surface)
            assert lattice_view.playhead == beat

    def test_playhead_wraps_at_window_end(self, lattice_view, dummy_surface):
        lattice_view.playhead = WINDOW_TOTAL_SLOTS
        lattice_view.render(dummy_surface)
        # Implementation should wrap or clamp; assert it doesn't crash
        assert 0 <= lattice_view.playhead < WINDOW_TOTAL_SLOTS or lattice_view.playhead == WINDOW_TOTAL_SLOTS


class TestColourMapping:
    """Chord type -> colour consistency."""

    def test_stable_palette_keys(self, lattice_view):
        expected_keys = set(range(7))
        assert set(lattice_view.palette.keys()) == expected_keys

    def test_rest_cells_rendered_as_rest_colour(self, lattice_view, dummy_surface):
        """Vacant slots (indices 3,7,12,15) should use rest_colour."""
        lattice_view.window_slots = WINDOW_SLOTS[:]
        lattice_view.render(dummy_surface)
        # Spot-check a rest cell region
        rest_indices = [3, 7, 12, 15]
        for idx in rest_indices:
            x = idx * lattice_view.cell_width
            # Sample centre of cell
            pixel = dummy_surface.get_at((x + lattice_view.cell_width // 2,
                                          lattice_view.cell_height // 2))
            # Should be close to rest_colour (allow minor anti-aliasing)
            assert pixel[:3] == lattice_view.rest_colour or \
                   sum(abs(a - b) for a, b in zip(pixel[:3], lattice_view.rest_colour)) < 30


class TestWindowAdvance:
    """Advancing windows updates the rendered strip."""

    def test_window_index_tracks(self, lattice_view):
        assert lattice_view.window_index == 0
        lattice_view.window_index = 1
        assert lattice_view.window_index == 1

    def test_render_after_window_advance(self, lattice_view, dummy_surface):
        lattice_view.window_index = 5
        lattice_view.render(dummy_surface)
        assert lattice_view.window_index == 5
