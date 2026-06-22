"""M0.T1: Project scaffold, deps, and import smoke tests."""
import os
import sys
import importlib
import pytest

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore


def _pkg_root() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "schellingchords")


def test_package_structure():
    """Verify project scaffold matches DESIGN.md §4 layout."""
    expected_files = ["__init__.py", "config.py", "model.py", "agents.py"]
    for fname in expected_files:
        path = os.path.join(_pkg_root(), fname)
        assert os.path.isfile(path), f"Missing scaffold file: {fname}"


def test_pyproject_deps():
    """Verify runtime and test dependencies are declared in pyproject.toml."""
    pyproject_path = os.path.join(os.path.dirname(__file__), "..", "pyproject.toml")
    assert os.path.isfile(pyproject_path), "pyproject.toml not found"
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)
    deps = data.get("project", {}).get("dependencies", [])
    dep_strs = [d.lower() for d in deps]
    assert any("mesa" in d for d in dep_strs), "mesa not in dependencies"
    assert any("pyyaml" in d for d in dep_strs), "pyyaml not in dependencies"
    assert any("numpy" in d for d in dep_strs), "numpy not in dependencies"


def test_imports_cleanly():
    """Package imports without side effects or missing module crashes."""
    mod = importlib.import_module("schellingchords")
    assert mod is not None
    # Allow empty __init__.py; no strict attribute checks to avoid false negatives
