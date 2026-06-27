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
    diffs = np.diff(avg_trend)
    # Freeze reconcile (Cale+Claude): faithful Schelling relocates each unsatisfied
    # agent to a UNIFORMLY RANDOM vacant slot, which can land it somewhere worse, so
    # segregation_index is a noisy upward DRIFT, not a monotone climb -- a 5-seed
    # average does not smooth the stochastic dips out. The original "<=1 down-step"
    # cap encoded a best-improving/monotone intuition the locked random rule violates.
    # G5 intent (segregation rises over a run) is preserved as: a robust net rise plus
    # up-steps outnumbering down-steps. (cf. the relocation-faithfulness decision.)
    assert avg_trend[-1] - avg_trend[0] >= 0.05
    assert np.sum(diffs > 1e-6) > np.sum(diffs < -1e-6)
