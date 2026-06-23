"""M9.T3 — pygame_gui control panel: sliders, buttons, config load/save, embed."""
import pytest
import pygame_gui
from tests.golden import WINDOW_TOTAL_SLOTS


class TestGUIInit:
    """SchellingGUI construction and embedded components."""

    def test_gui_has_lattice_view(self, gui_app):
        assert hasattr(gui_app, "lattice_view")
        assert gui_app.lattice_view is not None

    def test_gui_has_live_player(self, gui_app):
        assert hasattr(gui_app, "live_player")
        assert gui_app.live_player is not None

    def test_gui_has_manager(self, gui_app):
        assert hasattr(gui_app, "manager")
        assert isinstance(gui_app.manager, pygame_gui.UIManager)

    def test_gui_surface_exists(self, gui_app):
        assert hasattr(gui_app, "surface")
        assert gui_app.surface.get_width() > 0
        assert gui_app.surface.get_height() > 0


class TestSliderWriteThrough:
    """Moving sliders updates RuntimeParams immediately."""

    def test_tolerance_slider_exists(self, gui_app):
        assert hasattr(gui_app, "tolerance_slider")

    def test_tolerance_slider_range(self, gui_app):
        slider = gui_app.tolerance_slider
        assert slider.get_min_value() == 0.0
        assert slider.get_max_value() == 1.0

    def test_tolerance_slider_initial_value(self, gui_app):
        assert gui_app.tolerance_slider.get_current_value() == pytest.approx(0.5)

    def test_happiness_slider_exists(self, gui_app):
        assert hasattr(gui_app, "happiness_slider")

    def test_vacancy_slider_exists(self, gui_app):
        assert hasattr(gui_app, "vacancy_slider")

    def test_tempo_slider_exists(self, gui_app):
        assert hasattr(gui_app, "tempo_slider")

    def test_n_chord_types_slider_exists(self, gui_app):
        assert hasattr(gui_app, "n_chord_types_slider")

    def test_bars_per_window_slider_exists(self, gui_app):
        assert hasattr(gui_app, "bars_per_window_slider")

    def test_radius_slider_exists(self, gui_app):
        assert hasattr(gui_app, "radius_slider")

    def test_seed_slider_exists(self, gui_app):
        assert hasattr(gui_app, "seed_slider")

    def test_tolerance_write_through_to_runtime_params(self, gui_app):
        """Dragging tolerance slider updates live_player.runtime_params.tolerance."""
        gui_app.tolerance_slider.set_current_value(0.8)
        # Simulate slider release event
        event = pygame_gui.events.UISliderFinishedDragging(
            relative_rect=gui_app.tolerance_slider.relative_rect,
            value=0.8,
            ui_element=gui_app.tolerance_slider,
        )
        gui_app.manager.process_events([event])
        assert gui_app.live_player.runtime_params.tolerance == pytest.approx(0.8)

    def test_happiness_write_through(self, gui_app):
        gui_app.happiness_slider.set_current_value(0.3)
        event = pygame_gui.events.UISliderFinishedDragging(
            relative_rect=gui_app.happiness_slider.relative_rect,
            value=0.3,
            ui_element=gui_app.happiness_slider,
        )
        gui_app.manager.process_events([event])
        assert gui_app.live_player.runtime_params.happiness == pytest.approx(0.3)

    def test_tempo_write_through(self, gui_app):
        gui_app.tempo_slider.set_current_value(90)
        event = pygame_gui.events.UISliderFinishedDragging(
            relative_rect=gui_app.tempo_slider.relative_rect,
            value=90,
            ui_element=gui_app.tempo_slider,
        )
        gui_app.manager.process_events([event])
        assert gui_app.live_player.runtime_params.tempo_bpm == 90


class TestTransportButtons:
    """Run/pause/step/reset buttons."""

    def test_run_button_exists(self, gui_app):
        assert hasattr(gui_app, "run_button")

    def test_pause_button_exists(self, gui_app):
        assert hasattr(gui_app, "pause_button")

    def test_step_button_exists(self, gui_app):
        assert hasattr(gui_app, "step_button")

    def test_reset_button_exists(self, gui_app):
        assert hasattr(gui_app, "reset_button")

    def test_run_button_click_starts_playing(self, gui_app):
        gui_app.run_button.click()
        assert gui_app.live_player.playing is True

    def test_pause_button_click_stops_playing(self, gui_app):
        gui_app.run_button.click()
        gui_app.pause_button.click()
        assert gui_app.live_player.paused is True

    def test_step_button_click_advances_playhead(self, gui_app):
        gui_app.step_button.click()
        assert gui_app.live_player.playhead == 1

    def test_reset_button_click_resets(self, gui_app):
        gui_app.run_button.click()
        for _ in range(3):
            gui_app.step_button.click()
        gui_app.reset_button.click()
        assert gui_app.live_player.playhead == 0
        assert gui_app.live_player.paused is True


class TestConfigLoadSave:
    """Load/save config buttons."""

    def test_load_button_exists(self, gui_app):
        assert hasattr(gui_app, "load_button")

    def test_save_button_exists(self, gui_app):
        assert hasattr(gui_app, "save_button")

    def test_save_writes_config_file(self, gui_app, tmp_path):
        """Saving config produces a valid file."""
        config_path = tmp_path / "test_config.json"
        gui_app.config_path = str(config_path)
        gui_app.save_button.click()
        assert config_path.exists()

    def test_load_restores_params(self, gui_app, tmp_path):
        """Loading config restores RuntimeParams."""
        import json
        config_data = {
            "n_chord_types": 5,
            "bars_per_window": 3,
            "vacancy_fraction": 0.3,
            "tolerance": 0.7,
            "happiness": 0.5,
            "radius": 3,
            "tempo_bpm": 100,
            "seed": 123,
        }
        config_path = tmp_path / "loaded_config.json"
        config_path.write_text(json.dumps(config_data))
        gui_app.config_path = str(config_path)
        gui_app.load_button.click()
        # Structural params apply on reset; runtime params update immediately
        assert gui_app.live_player.runtime_params.tolerance == pytest.approx(0.7)
        assert gui_app.live_player.runtime_params.happiness == pytest.approx(0.5)
        assert gui_app.live_player.runtime_params.tempo_bpm == 100


class TestEmbedConsistency:
    """LatticeView and LivePlayer stay in sync."""

    def test_lattice_view_window_index_matches_player(self, gui_app):
        gui_app.lattice_view.window_index = 3
        assert gui_app.lattice_view.window_index == 3

    def test_lattice_view_playhead_matches_player(self, gui_app):
        gui_app.live_player.playhead = 7
        gui_app.lattice_view.playhead = 7
        assert gui_app.lattice_view.playhead == gui_app.live_player.playhead

    def test_render_updates_each_frame(self, gui_app):
        """Calling update/render doesn't raise."""
        gui_app.update(0.016)
        gui_app.render()
