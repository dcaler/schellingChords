"""Shared fixtures and cross-module window constants for the SchellingChords suite.

OWNED BY P0.T0 (the harness/fixtures freeze). The per-module P0.M* authoring tasks
must NOT overwrite this file — doing so previously clobbered fixtures from earlier
modules (e.g. M9's run wiped the M3 agent-window constants). The doer enforces this:
only P0.T0 may write tests/conftest.py and tests/golden/__init__.py.

Two kinds of shared state live here:
  * Module-level constants imported by tests (`from tests.conftest import WINDOW_CHORDS`).
  * pytest fixtures referenced by name across modules.
"""
import os

import pytest

# Force headless SDL drivers before pygame is imported/initialised (M9 GUI/viz tests).
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_NOMOUSE", "1")

import pygame          # noqa: E402  (must follow the SDL_* env setup above)
import pygame_gui      # noqa: E402,F401

# ---------------------------------------------------------------------------
# M3 agent-window constants (Cale+Claude freeze reconcile).
#
# A 16-slot 1D window hand-built so the FROZEN M3 goldens hold under radius=2,
# tolerance=0.6, Jaccard distance (see tests/golden):
#   * idx 2  = "C"  surrounded by C   -> satisfaction 1.0 (dist 0.0 <= tol)
#   * idx 8  = "F"  surrounded by Bdim -> satisfaction 0.0 (dist 0.8 > tol)
#   * idx 14 placed agent sees only vacant neighbours {12,13,15} -> vacuously 1.0
#   * "F" at 8 relocating: slot 12 -> 1/3, slot 13 -> 1/2, slot 15 -> 1/1 (next to
#     Dm, dist 0.5 <= tol); best empty slot = 15.
# Occupied = {0..11, 14}; vacant = {12, 13, 15}. Vacant WINDOW_CHORDS entries are
# never read (neighbour scans filter on WINDOW_SLOTS == 1; agents sit at 2/8/14).
# ---------------------------------------------------------------------------
WINDOW_TOTAL_SLOTS: int = 16
WINDOW_CHORDS: list = [
    "C", "C", "C", "C", "C", "C",        # 0-5
    "Bdim", "Bdim", "F", "Bdim", "Bdim", "Bdim",  # 6-11
    None, None, "Dm", None,              # 12-15  (12,13,15 vacant; 14 = Dm)
]
WINDOW_SLOTS: list = [1 if c is not None else 0 for c in WINDOW_CHORDS]
WINDOW_VACANT_INDICES: list = [i for i, s in enumerate(WINDOW_SLOTS) if not s]


@pytest.fixture
def window_config():
    """Scalar params the M3 satisfaction / desired-slot tests evaluate their goldens
    against. tolerance 0.6 makes dist(C,C)=0 satisfy and dist(F,Bdim)=0.8 not."""
    return {"radius": 2, "tolerance": 0.6, "happiness": 0.6, "seed": 42}


# ---------------------------------------------------------------------------
# Config fixtures. `Config` is the canonical dataclass name (DESIGN.md, config.py).
# ---------------------------------------------------------------------------
_CONFIG_KWARGS = dict(
    n_chord_types=7,
    bars_per_window=4,
    vacancy_fraction=0.25,
    tolerance=0.5,
    happiness=0.6,
    radius=2,
    tempo_bpm=120,
    seed=42,
)


@pytest.fixture
def base_config():
    """Canonical Config instance used across M9 tests."""
    from schellingchords.config import Config
    return Config(**_CONFIG_KWARGS)


@pytest.fixture
def config():
    """Same canonical Config, under the name the M4/observable/golden tests use."""
    from schellingchords.config import Config
    return Config(**_CONFIG_KWARGS)


@pytest.fixture
def chord_population():
    """Placeholder population fixture: present so model tests that accept it as a
    parameter collect and run; the model builds its own population from Config."""
    return None


@pytest.fixture
def window_with_vacancies():
    """The M3 window as (slots, chords); a convenience handle for model tests."""
    return list(WINDOW_SLOTS), list(WINDOW_CHORDS)


# ---------------------------------------------------------------------------
# M9 GUI / viz fixtures (headless).
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _pygame_headless():
    """Initialise pygame in dummy/headless mode for every test."""
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


@pytest.fixture
def dummy_surface():
    """800x600 pygame Surface for rendering assertions."""
    return pygame.Surface((800, 600))


@pytest.fixture
def model(base_config):
    """Freshly seeded 1D Schelling model."""
    from schellingchords.model import SchellingChordModel
    return SchellingChordModel(config=base_config)


@pytest.fixture
def live_player(model):
    """LivePlayer wired to *model*, ready for tick-driven tests."""
    from schellingchords.player import LivePlayer
    return LivePlayer(model=model)


@pytest.fixture
def lattice_view():
    """LatticeView sized for the default 16-slot window."""
    from schellingchords.viz import LatticeView
    return LatticeView(width=800, height=200, n_chord_types=7)


@pytest.fixture
def gui_app(base_config):
    """Minimal pygame_gui application embedding LatticeView + LivePlayer."""
    from schellingchords.gui import SchellingGUI
    return SchellingGUI(config=base_config)
