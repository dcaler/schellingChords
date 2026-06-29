import argparse
import csv
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence

from schellingchords.agents import ChordAgent
from schellingchords.config import Config
from schellingchords.metrics import jaccard_distance
from schellingchords.model import SchellingChordModel, _NeighborView
from schellingchords.sonify import trajectory_to_midi


def _happy_count(window: List[Optional[str]], params) -> int:
    """Count occupied slots whose agent is satisfied.

    Uses the canonical ``ChordAgent.is_satisfied`` rule via the same probe +
    ``_NeighborView`` pattern as ``SchellingChordModel.step``, so "what counts as
    happy" is defined in exactly one place. (Earlier revisions re-implemented the
    Jaccard/tolerance test inline here; that duplication is what dragged in a stray
    ``jaccard_distance`` reference and let satisfaction drift from the model.)
    """
    metric = jaccard_distance
    view = _NeighborView(window, params.radius)
    probe = ChordAgent(unique_id=-1, model=None)
    count = 0
    for i, name in enumerate(window):
        if name is None:
            continue
        probe.chord_name = name
        if probe.is_satisfied(view[i], metric, params.tolerance, params.happiness):
            count += 1
    return count


def single(config_path: str, out_dir: str) -> None:
    """Run the model once; write per-window MIDI and an observables CSV.

    Outputs use the dated naming convention ({YYMMDD}_{project}_...). The CSV
    carries one row per simulation step with the model observables plus ``step``
    and ``happy_agents`` columns.
    """
    config = Config.load_yaml(config_path)

    out_dir_path = Path(out_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)
    prefix = f"{datetime.now().strftime('%y%m%d')}_schellingchords"

    model = SchellingChordModel(config)
    history = model.run(config.n_steps)

    # Per-window MIDI.
    for w_idx, window in enumerate(history):
        out_path = out_dir_path / f"{prefix}_window_{w_idx + 1}.mid"
        pm = trajectory_to_midi([window], config)
        pm.write(str(out_path))

    # Observables CSV: model vars + step + happy_agents (one row per step).
    df = model.datacollector.get_model_vars_dataframe()
    df["step"] = range(1, len(df) + 1)
    df["happy_agents"] = [_happy_count(window, model.params) for window in history]
    df.to_csv(out_dir_path / f"{prefix}_observables.csv", index=False)


def sweep(
    config_path: str,
    param_name: str,
    values: Sequence[float],
    out_dir: str,
) -> None:
    """Sweep one config parameter; write a single phase-diagram summary CSV.

    Produces exactly one CSV with one row per swept value: the value itself (in a
    column named after the parameter) alongside the final-state aggregate
    observables for that run. This is a summary, not a per-step trajectory dump.
    """
    base = Config.load_yaml(config_path)

    out_dir_path = Path(out_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)
    prefix = f"{datetime.now().strftime('%y%m%d')}_schellingchords"

    fieldnames = [
        param_name,
        "segregation_index",
        "region_count",
        "happy_agents",
        "happy_fraction",
    ]
    rows = []
    for value in values:
        # Config is a frozen dataclass; replace() returns a validated new instance.
        cfg = replace(base, **{param_name: value})
        model = SchellingChordModel(cfg)
        model.run(cfg.n_steps)

        final_window = model.window
        n_occupied = sum(1 for s in final_window if s is not None)
        happy = _happy_count(final_window, model.params)
        rows.append({
            param_name: value,
            "segregation_index": model._get_segregation_index(),
            "region_count": model._get_region_count(),
            "happy_agents": happy,
            "happy_fraction": (happy / n_occupied) if n_occupied else 0.0,
        })

    csv_path = out_dir_path / f"{prefix}_sweep_{param_name}.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _parse_scalar(s: str):
    """Parse a sweep value as int when it has no fractional part, else float."""
    try:
        return int(s)
    except ValueError:
        return float(s)


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        prog="schellingchords",
        description="Run the SchellingChords model once, or sweep a parameter.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_single = sub.add_parser(
        "single", help="Run once; write per-window MIDI + observables CSV."
    )
    p_single.add_argument("config", help="Path to a YAML config file.")
    p_single.add_argument(
        "-o", "--out-dir", default="outputs", help="Output directory."
    )

    p_sweep = sub.add_parser(
        "sweep", help="Vary one parameter; write a summary CSV (one row per value)."
    )
    p_sweep.add_argument("config", help="Path to a YAML config file.")
    p_sweep.add_argument("param", help="Config field to vary (e.g. tolerance).")
    p_sweep.add_argument(
        "values", nargs="+", help="One or more values to sweep, e.g. 0.3 0.5 0.7"
    )
    p_sweep.add_argument(
        "-o", "--out-dir", default="sweep_outputs", help="Output directory."
    )

    args = parser.parse_args(argv)
    if args.command == "single":
        single(args.config, args.out_dir)
    elif args.command == "sweep":
        values = [_parse_scalar(v) for v in args.values]
        sweep(args.config, args.param, values, args.out_dir)


if __name__ == "__main__":
    main()
