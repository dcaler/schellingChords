import pytest
from typing import Any, Dict, List, Tuple


@pytest.fixture
def config() -> Dict[str, Any]:
    """Base configuration for the SchellingChords model."""
    return {
        "width": 5,
        "height": 5,
        "threshold": 0.5,
        "radius": 1,
        "seed": 42,
        "vacancy_ratio": 0.2,
    }


@pytest.fixture
def small_chord_population() -> List[Dict[str, Any]]:
    """Small, deterministic chord population for unit tests."""
    return [
        {"name": "C_MAJ", "pcs": [0, 4, 7]},
        {"name": "A_MIN", "pcs": [9, 0, 4]},
        {"name": "D_MIN", "pcs": [2, 5, 9]},
        {"name": "G_MAJ", "pcs": [7, 11, 2]},
    ]


@pytest.fixture
def grid_with_vacancies() -> List[List[int]]:
    """5x5 grid with exactly 6 occupied cells (1) and 19 vacancies (0)."""
    return [
        [1, 1, 0, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 0, 0, 1],
        [0, 0, 0, 1, 0],
        [1, 0, 0, 0, 0],
    ]


@pytest.fixture
def occupied_coords() -> List[Tuple[int, int]]:
    """Coordinates corresponding to the 1s in grid_with_vacancies."""
    return [(0, 0), (0, 1), (1, 2), (2, 4), (3, 3), (4, 0)]


@pytest.fixture
def tmp_outputs_dir(tmp_path):
    """Temporary directory for model outputs."""
    out_dir = tmp_path / "outputs"
    out_dir.mkdir()
    return out_dir
