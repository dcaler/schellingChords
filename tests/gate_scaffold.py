"""G0: Module gate — installed package imports and configs/default.yaml loads."""
import os
import importlib
import pytest


def test_g0_package_imports():
    """G0: Installed package imports successfully."""
    mod = importlib.import_module("schellingchords")
    assert mod is not None


def test_g0_default_yaml_loads():
    """G0: configs/default.yaml loads into a valid Config (T1+T2)."""
    yaml_path = os.path.join(os.path.dirname(__file__), "..", "configs", "default.yaml")
    assert os.path.isfile(yaml_path), "configs/default.yaml must exist for gate"
    
    mod = importlib.import_module("schellingchords.config")
    Config = mod.Config
    cfg = Config.load_yaml(yaml_path)
    
    assert isinstance(cfg, Config)
    assert 0 <= cfg.vacancy_fraction < 1
    assert cfg.n_chord_types >= 2
    assert cfg.bars_per_window > 0
    assert cfg.radius >= 0
