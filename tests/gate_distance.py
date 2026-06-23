import pytest
from schellingchords.metrics.registry import get_metric
from tests.golden import DIATONIC_CHORDS


@pytest.fixture
def metric():
    return get_metric("pitch_class_overlap")


def test_gate_ordering_iv_closer_than_ivii(metric):
    """G2: I–V (share G) closer than I–vii°"""
    i = DIATONIC_CHORDS["C"]
    v = DIATONIC_CHORDS["G"]
    vii = DIATONIC_CHORDS["Bdim"]

    dist_iv = metric.distance(i, v)
    dist_ivii = metric.distance(i, vii)

    assert dist_iv < dist_ivii, f"Expected I-V ({dist_iv}) < I-vii° ({dist_ivii})"


def test_gate_triangle_inequality_spot(metric):
    """G2: Triangle inequality spot check (T1+T2+M1)"""
    i = DIATONIC_CHORDS["C"]
    iii = DIATONIC_CHORDS["Em"]
    v = DIATONIC_CHORDS["G"]

    d_i_iii = metric.distance(i, iii)
    d_iii_v = metric.distance(iii, v)
    d_i_v = metric.distance(i, v)

    # d(i, v) <= d(i, iii) + d(iii, v)
    assert d_i_v <= d_i_iii + d_iii_v + 1e-9, "Triangle inequality violated"
