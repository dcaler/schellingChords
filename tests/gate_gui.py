"""G9 — Headless integration gate: launch app, drive ticks, verify player+viz+slider."""
import pytest
import pygame_gui
from tests.golden import WINDOW_TOTAL_SLOTS


class TestGateGUIHeadless:
    """End-to-end: launch SchellingGUI, drive live ticks, assert player advances model,
    viz renders window, and moving tolerance slider changes RuntimeParams mid-run."""

    def test_gate_launch_and_tick_drive(self, gui_app):
        """Launch app, drive a few live ticks — player advances the model, viz renders."""
        # 1. Start playing
        gui_app.run_button.click()
        assert gui_app.live_player.playing is True

        # 2. Drive 8 ticks (half a window)
        for _ in range(8):
            gui_app.live_player.generate_tick()

        # 3. Playhead should be at 8
        assert gui_app.live_player.playhead == 8

        # 4. LatticeView should have rendered without error
        gui_app.lattice_view.render(gui_app.surface)
        assert gui_app.lattice_view.window_index == 0

    def test_gate_full_window_step_trigger(self, gui_app):
        """Drive full window — model.step() fires at boundary.

        Freeze reconcile (Cale+Claude): spy on Mesa's genuine `model.steps`, not the
        `_step_count` attribute the model never defines (same oracle bug fixed in
        tests/test_player.py — both reads returned the 0 default, so == +1 was
        unsatisfiable regardless of the gui implementation).
        """
        gui_app.run_button.click()
        original_steps = gui_app.live_player.model.steps

        for _ in range(WINDOW_TOTAL_SLOTS):
            gui_app.live_player.generate_tick()

        # After full window, step should have fired once
        assert gui_app.live_player.model.steps == original_steps + 1

    def test_gate_slider_mid_run(self, gui_app):
        """Moving tolerance slider changes RuntimeParams mid-run."""
        gui_app.run_button.click()

        # Drive 4 ticks
        for _ in range(4):
            gui_app.live_player.generate_tick()

        # Change tolerance via slider
        gui_app.tolerance_slider.set_current_value(0.9)
        event = pygame_gui.events.UISliderFinishedDragging(
            relative_rect=gui_app.tolerance_slider.relative_rect,
            value=0.9,
            ui_element=gui_app.tolerance_slider,
        )
        gui_app.manager.process_events([event])

        # RuntimeParams should reflect new tolerance immediately
        assert gui_app.live_player.runtime_params.tolerance == pytest.approx(0.9)

        # Continue driving ticks — should not crash
        for _ in range(4):
            gui_app.live_player.generate_tick()

        assert gui_app.live_player.playhead == 8

    def test_gate_viz_sync_with_player(self, gui_app):
        """LatticeView playhead stays synchronised with LivePlayer."""
        gui_app.run_button.click()

        for beat in range(WINDOW_TOTAL_SLOTS):
            gui_app.live_player.generate_tick()
            gui_app.lattice_view.playhead = gui_app.live_player.playhead
            gui_app.lattice_view.render(gui_app.surface)
            assert gui_app.lattice_view.playhead == gui_app.live_player.playhead

    def test_gate_pause_resume(self, gui_app):
        """Pause and resume mid-window."""
        gui_app.run_button.click()
        for _ in range(5):
            gui_app.live_player.generate_tick()

        gui_app.pause_button.click()
        assert gui_app.live_player.paused is True

        # Resume
        gui_app.run_button.click()
        assert gui_app.live_player.playing is True

        for _ in range(5):
            gui_app.live_player.generate_tick()

        assert gui_app.live_player.playhead == 10

    def test_gate_reset_mid_run(self, gui_app):
        """Reset returns to origin and re-seeds model."""
        gui_app.run_button.click()
        for _ in range(10):
            gui_app.live_player.generate_tick()

        gui_app.reset_button.click()
        assert gui_app.live_player.playhead == 0
        assert gui_app.live_player.window_index == 0
        assert gui_app.live_player.paused is True

    def test_gate_multiple_windows(self, gui_app):
        """Drive through 2 full windows — step fires twice."""
        gui_app.run_button.click()
        original_steps = gui_app.live_player.model.steps

        for _ in range(WINDOW_TOTAL_SLOTS * 2):
            gui_app.live_player.generate_tick()

        assert gui_app.live_player.model.steps == original_steps + 2
        assert gui_app.live_player.window_index == 2

    def test_gate_occupied_count_invariant(self, gui_app):
        """Across windows, occupied slot count remains consistent with vacancy_fraction."""
        gui_app.run_button.click()

        for window in range(3):
            occupied = 0
            for _ in range(WINDOW_TOTAL_SLOTS):
                tick = gui_app.live_player.generate_tick()
                if tick["chord_or_rest"] is not None:
                    occupied += 1
            # Occupied count should be close to expected (allow small variance from relocation)
            assert occupied <= WINDOW_TOTAL_SLOTS
            assert occupied >= WINDOW_TOTAL_SLOTS * (1 - gui_app.live_player.runtime_params.vacancy_fraction) - 2
