import os
import tempfile
import pandas as pd
from schellingchords.config import Config
from schellingchords.model import SchellingChordModel
from schellingchords.observables import segregation_index
from schellingchords.sonify import trajectory_to_midi

def _chord_distance(a: str, b: str) -> float:
    """Simple distance metric: 0.0 if same chord, 1.0 otherwise."""
    return 0.0 if a == b else 1.0

def run_pipeline(config_path: str) -> str:
    cfg = Config.load_yaml(config_path)
    model = SchellingChordModel(cfg)
    
    n_steps = getattr(cfg, 'n_steps', 50)
    history = model.run(n_steps)
    
    rows = []
    for step, window in enumerate(history):
        seg_idx = segregation_index(window, _chord_distance, cfg.tolerance, cfg.radius)
        rows.append({"step": step, "segregation_index": seg_idx})
        
    df = pd.DataFrame(rows)
    
    out_dir = tempfile.mkdtemp()
    df.to_csv(os.path.join(out_dir, "observables.csv"), index=False)
    
    pm = trajectory_to_midi(history, cfg)
    pm.write(os.path.join(out_dir, "output.mid"))
    
    return out_dir
