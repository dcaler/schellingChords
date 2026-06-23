"""Shared fixtures for SchellingChords M9 tests."""
import os
import pytest
import pygame
import pygame_gui

# Force headless drivers before any pygame init
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_NOMOUSE", "1")


@pytest.fixture(autouse=True)
def _pygame_headless():
    """Ensure pygame is initialised in dummy/headless mode for every test."""
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


@pytest.fixture
def dummy_surface():
    """800×600 pygame Surface for rendering assertions."""
    return pygame.Surface((800, 600))


@pytest.fixture
def base_config():
    """Canonical Config dataclass instance used across M9 tests."""
    from schellingchords.config import Config
    return Config(
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
def model(base_config):
    """Return a freshly seeded Schelling model (1D window)."""
    from schellingchords.model import SchellingModel
    return SchellingModel(config=base_config)


@pytest.fixture
def live_player(model):
    """LivePlayer wired to *model*, ready for tick-driven tests."""
    from schellingchords.player import LivePlayer
    return LivePlayer(model=model)


@pytest.fixture
def lattice_view():
    """LatticeView instance sized for the default 16-slot window."""
    from schellingchords.viz import LatticeView
    return LatticeView(width=800, height=200, n_chord_types=7)


@pytest.fixture
def gui_app(base_config):
    """Minimal pygame_gui application embedding LatticeView + LivePlayer."""
    from schellingchords.gui import SchellingGUI
    return SchellingGUI(config=base_config)
