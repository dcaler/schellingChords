import pytest
import pandas as pd

@pytest.fixture
def mock_history():
    # 3 steps, 4 slots. Pos 3 changes at step 2.
    return [
        ["C", "C", None, "Em"],
        ["C", "C", None, "Em"],
        ["C", "C", None, "Dm"],
    ]

def test_stability_profile_shape_and_values(mock_history):
    from schellingchords.observables import stability_profile

    profile = stability_profile(mock_history)
    assert len(profile) == 4
    assert all(isinstance(v, float) and 0.0 <= v <= 1.0 for v in profile)
    # Positions 0, 1, 2 are stable across all steps
    assert profile[0] == 1.0
    assert profile[1] == 1.0
    assert profile[2] == 1.0
    # Position 3 changes, so settledness < 1.0
    assert profile[3] < 1.0

def test_datacollector_wiring():
    from schellingchords.model import SchellingChordModel
    from schellingchords.config import Config
    from mesa import DataCollector

    model = SchellingChordModel(Config(
        n_chord_types=3, bars_per_window=4, vacancy_fraction=0.25,
        tolerance=0.6, happiness=0.5, radius=2, tempo_bpm=120, seed=42
    ))
    assert isinstance(model.datacollector, DataCollector)
    assert "segregation_index" in model.datacollector.model_vars
    assert "region_count" in model.datacollector.model_vars

    for _ in range(3):
        model.step()

    df = model.datacollector.get_model_vars_dataframe()
    assert len(df) == 3
    assert "segregation_index" in df.columns
    assert "region_count" in df.columns
