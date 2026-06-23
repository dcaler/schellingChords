import os
import pytest
import pandas as pd

class TestSystemGateG8:
    def test_headless_pipeline_runs(self):
        from schellingchords.runner import run_pipeline
        output_dir = run_pipeline("configs/demo.yaml")
        assert output_dir is not None

    def test_segregation_demonstrable(self):
        from schellingchords.runner import run_pipeline
        output_dir = run_pipeline("configs/demo.yaml")
        obs = pd.read_csv(os.path.join(output_dir, "observables.csv"))
        assert obs["segregation_index"].iloc[-1] > obs["segregation_index"].iloc[0]
        assert obs["segregation_index"].std() > 0.0

    def test_midi_deliverable_valid(self):
        from schellingchords.runner import run_pipeline
        output_dir = run_pipeline("configs/demo.yaml")
        midi_path = os.path.join(output_dir, "output.mid")
        assert os.path.getsize(midi_path) > 0
        import mido
        mid = mido.MidiFile(midi_path)
        assert len(mid.tracks) > 0
