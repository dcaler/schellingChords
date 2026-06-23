import pytest
import numpy as np

def test_gate_observables_trend():
    from schellingchords.model import SchellingChordModel
    from schellingchords.config import Config

    seeds = [1, 2, 3, 4, 5]
    n_steps = 10
    all_runs = []

    for seed in seeds:
        model = SchellingChordModel(Config(
            n_chord_types=3, bars_per_window=4, vacancy_fraction=0.25,
            tolerance=0.6, happiness=0.5, radius=2, tempo_bpm=120, seed=seed
        ))
        for _ in range(n_steps):
            model.step()
        df = model.datacollector.get_model_vars_dataframe()
        all_runs.append(df["segregation_index"].values)

    avg_trend = np.mean(all_runs, axis=0)
    # G5: mean segregation_index is non-decreasing over a multi-run average
    assert avg_trend[-1] >= avg_trend[0] - 1e-6
    # Allow minor stochastic dips but overall trend must be non-decreasing
    diffs = np.diff(avg_trend)
    assert np.sum(diffs < -1e-6) <= 1
