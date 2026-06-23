import os
import pytest
import yaml
from tests.golden import DIATONIC_CHORDS, DISTANCES

@pytest.fixture
def demo_yaml_path():
    return os.path.join("configs", "demo.yaml")

@pytest.fixture
def loaded_demo_config(demo_yaml_path):
    with open(demo_yaml_path, "r") as f:
        return yaml.safe_load(f)

class TestEndToEndAcceptance:
    def test_config_loads_and_matches_schema(self, loaded_demo_config):
        required_keys = {
            "n_chord_types", "bars_per_window", "vacancy_fraction",
            "tolerance", "happiness", "radius", "tempo_bpm", "seed"
        }
        assert required_keys.issubset(loaded_demo_config.keys())

    def test_model_run_produces_deliverables(self, demo_yaml_path):
        from schellingchords.runner import run_pipeline
        output_dir = run_pipeline(demo_yaml_path)
        assert os.path.isdir(output_dir)
        assert os.path.exists(os.path.join(output_dir, "output.mid"))
        assert os.path.exists(os.path.join(output_dir, "observables.csv"))

    def test_segregation_increases_over_time(self, demo_yaml_path):
        from schellingchords.runner import run_pipeline
        import pandas as pd
        output_dir = run_pipeline(demo_yaml_path)
        obs_path = os.path.join(output_dir, "observables.csv")
        df = pd.read_csv(obs_path)
        assert "step" in df.columns
        assert "segregation_index" in df.columns
        first_idx = df.iloc[0]["segregation_index"]
        final_idx = df.iloc[-1]["segregation_index"]
        assert final_idx > first_idx, "Segregation must increase over simulation steps"

    def test_deterministic_under_seed(self, demo_yaml_path):
        from schellingchords.runner import run_pipeline
        import pandas as pd
        out1 = run_pipeline(demo_yaml_path)
        df1 = pd.read_csv(os.path.join(out1, "observables.csv"))
        out2 = run_pipeline(demo_yaml_path)
        df2 = pd.read_csv(os.path.join(out2, "observables.csv"))
        pd.testing.assert_frame_equal(df1, df2)
