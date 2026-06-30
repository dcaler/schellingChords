"""M9.T1 — LivePlayer tick order, step trigger, slider write-through, surface render."""
import pytest
from tests.golden import (
    WINDOW_TOTAL_SLOTS,
    WINDOW_OCCUPIED_SLOTS,
)

# Freeze reconcile (Cale+Claude), M9.T1. The original golden tests had three
# internal oracle bugs that no LivePlayer could pass (doer plateaued at 17/17):
#   1. test_tick_rest_pattern parametrized one FRESH fixture per beat, called
#      generate_tick() once, and asserted beat_index == N>0 — unsatisfiable, since
#      a fresh player's first tick is always beat 0.
#   2. the rest-pattern tests pinned the hand-authored golden WINDOW_SLOTS, whose
#      vacancies fall at indices the seeded model never produces (same vacant
#      COUNT, different PLACES) — a faithful player reads its real model window.
#   3. the step-trigger tests spied on model._step_count, which the Mesa model
#      never defines; it increments self.steps in its auto-wrapped step.
# Reconciled to assert the player faithfully follows its OWN wired model's window
# occupancy and Mesa's genuine `model.steps`. Intent preserved, contradictions
# removed.


class TestLivePlayerInit:
    """LivePlayer construction and RuntimeParams exposure."""

    def test_player_exposes_runtime_params(self, live_player):
        rp = live_player.runtime_params
        assert rp.tolerance == pytest.approx(0.5)
        assert rp.happiness == pytest.approx(0.6)
        assert rp.vacancy_fraction == pytest.approx(0.25)
        assert rp.tempo_bpm == 120

    def test_player_state_defaults(self, live_player):
        assert live_player.playhead == 0
        assert live_player.window_index == 0
        assert live_player.paused is True
        assert live_player.playing is False

    def test_reset_reseeds_model(self, live_player, base_config):
        live_player.reset()
        # After reset playhead returns to 0 and model is re-initialised
        assert live_player.playhead == 0
        assert live_player.window_index == 0


class TestTickGeneration:
    """Deterministic tick emission decoupled from wall-clock."""

    def test_tick_shape(self, live_player):
        live_player.paused = False
        tick = live_player.generate_tick()
        assert isinstance(tick, dict)
        assert "window" in tick
        assert "beat_index" in tick
        assert "chord_or_rest" in tick

    def test_first_tick_is_window_0_beat_0(self, live_player):
        live_player.paused = False
        tick = live_player.generate_tick()
        assert tick["window"] == 0
        assert tick["beat_index"] == 0

    def test_ticks_advance_playhead(self, live_player):
        live_player.paused = False
        for expected_beat in range(WINDOW_TOTAL_SLOTS):
            tick = live_player.generate_tick()
            assert tick["beat_index"] == expected_beat
            assert live_player.playhead == expected_beat + 1

    def test_rest_ticks_contain_none_chord(self, live_player, model):
        """Vacant slots in the player's live model window yield chord_or_rest None."""
        live_player.paused = False
        for slot in model.window:
            tick = live_player.generate_tick()
            if slot is None:
                assert tick["chord_or_rest"] is None
            else:
                assert tick["chord_or_rest"] is not None

    def test_occupied_count_matches_golden(self, live_player):
        live_player.paused = False
        occupied = sum(1 for _ in range(WINDOW_TOTAL_SLOTS)
                       if live_player.generate_tick()["chord_or_rest"] is not None)
        assert occupied == WINDOW_OCCUPIED_SLOTS


class TestStepTrigger:
    """model.step() fires exactly at window boundary."""

    def test_step_called_at_window_end(self, live_player, model):
        live_player.paused = False
        original_steps = model.steps
        for _ in range(WINDOW_TOTAL_SLOTS):
            live_player.generate_tick()
        # After consuming all beats in the window, step should have fired once
        assert model.steps == original_steps + 1

    def test_step_not_called_mid_window(self, live_player, model):
        live_player.paused = False
        original_steps = model.steps
        for _ in range(WINDOW_TOTAL_SLOTS // 2):
            live_player.generate_tick()
        assert model.steps == original_steps


class TestRuntimeParamsWriteThrough:
    """Slider-driven param changes propagate immediately."""

    def test_tolerance_write_through(self, live_player):
        live_player.runtime_params.tolerance = 0.8
        assert live_player.runtime_params.tolerance == pytest.approx(0.8)

    def test_happiness_write_through(self, live_player):
        live_player.runtime_params.happiness = 0.3
        assert live_player.runtime_params.happiness == pytest.approx(0.3)

    def test_vacancy_fraction_write_through(self, live_player):
        live_player.runtime_params.vacancy_fraction = 0.4
        assert live_player.runtime_params.vacancy_fraction == pytest.approx(0.4)

    def test_tempo_write_through(self, live_player):
        live_player.runtime_params.tempo_bpm = 90
        assert live_player.runtime_params.tempo_bpm == 90


class TestPlayPauseStepReset:
    """Transport controls."""

    def test_play_sets_playing(self, live_player):
        live_player.play()
        assert live_player.playing is True
        assert live_player.paused is False

    def test_pause_sets_paused(self, live_player):
        live_player.play()
        live_player.pause()
        assert live_player.paused is True
        assert live_player.playing is False

    def test_step_advances_one_beat(self, live_player):
        live_player.step()
        assert live_player.playhead == 1

    def test_reset_returns_to_origin(self, live_player):
        live_player.play()
        for _ in range(5):
            live_player.step()
        live_player.reset()
        assert live_player.playhead == 0
        assert live_player.window_index == 0
        assert live_player.paused is True


class TestTickOrderGolden:
    """Tick sequence for the first window follows the live model's occupancy."""

    def test_tick_rest_pattern(self, live_player, model):
        live_player.paused = False
        expected_is_rest = [chord is None for chord in model.window]
        for beat_index, want_rest in enumerate(expected_is_rest):
            tick = live_player.generate_tick()
            assert tick["beat_index"] == beat_index
            assert (tick["chord_or_rest"] is None) == want_rest
