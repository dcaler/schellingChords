import pytest

@pytest.fixture
def window_total_slots():
    """1D window: 4 bars * 4 beats/bar = 16 beat-slots"""
    return 16

@pytest.fixture
def window_occupied_slots():
    """Occupied beats = total * (1 - vacancy_fraction) = 16 * 0.75 = 12"""
    return 12

@pytest.fixture
def window_slots():
    """Flat 1D representation: 1 = occupied chord, 0 = vacant rest"""
    return [1] * 12 + [0] * 4

@pytest.fixture
def window_occupied_indices():
    """Integer indices of occupied beat-slots in the 1D window"""
    return list(range(12))

@pytest.fixture
def demo_config_kwargs():
    return {
        "n_chord_types": 4,
        "bars_per_window": 4,
        "vacancy_fraction": 0.25,
        "tolerance": 0.5,
        "happiness": 0.6,
        "radius": 2,
        "tempo_bpm": 120,
        "seed": 42,
    }
