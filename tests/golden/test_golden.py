import pytest
from tests.golden import CHORD_REGISTRY, OVERLAP_CASES, DISTANCE_CASES


@pytest.mark.parametrize("chord_a_name, chord_b_name, expected_overlap", OVERLAP_CASES)
def test_pitch_class_overlap(chord_a_name, chord_b_name, expected_overlap):
    """Assert overlap matches hand-computed golden values."""
    from schellingchords.metrics import pitch_class_overlap
    set_a = set(CHORD_REGISTRY[chord_a_name])
    set_b = set(CHORD_REGISTRY[chord_b_name])
    assert pitch_class_overlap(set_a, set_b) == expected_overlap


@pytest.mark.parametrize("chord_a_name, chord_b_name, expected_distance", DISTANCE_CASES)
def test_pitch_class_distance(chord_a_name, chord_b_name, expected_distance):
    """Assert distance matches hand-computed golden values (12 - overlap)."""
    from schellingchords.metrics import pitch_class_distance
    set_a = set(CHORD_REGISTRY[chord_a_name])
    set_b = set(CHORD_REGISTRY[chord_b_name])
    assert pitch_class_distance(set_a, set_b) == expected_distance


def test_grid_fixture_consistency(grid_with_vacancies, occupied_coords):
    """Verify internal consistency of grid and coordinate fixtures."""
    total_ones = sum(sum(row) for row in grid_with_vacancies)
    assert total_ones == len(occupied_coords), "Occupied count mismatch"
    assert total_ones == 6, "Expected exactly 6 occupied cells"

    width = len(grid_with_vacancies[0])
    height = len(grid_with_vacancies)
    assert width * height == 25, "Grid dimensions mismatch"

    # Every 1 must be in occupied_coords
    for r in range(height):
        for c in range(width):
            if grid_with_vacancies[r][c] == 1:
                assert (r, c) in occupied_coords

    # Every coord must be a 1
    for r, c in occupied_coords:
        assert grid_with_vacancies[r][c] == 1


def test_config_fixture_structure(config):
    """Verify config fixture contains required keys."""
    required_keys = {"width", "height", "threshold", "radius", "seed", "vacancy_ratio"}
    assert set(config.keys()) == required_keys
