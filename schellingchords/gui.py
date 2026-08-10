"""M9.T3 — pygame_gui control panel wrapping LivePlayer + LatticeView.

Presentation layer only: sliders write straight through to the shared
``RuntimeParams`` object, transport buttons drive the ``LivePlayer``, and
load/save round-trip the runtime params to ``config_path`` as JSON.

Targets the standalone ``pygame_gui`` 0.6.x API: horizontal sliders are
``UIHorizontalSlider`` and a slider drag emits a pygame event of type
``pygame_gui.UI_HORIZONTAL_SLIDER_MOVED`` (there is no ``pygame_gui.events``
submodule and no ``UISlider`` class).
"""
import json
import os
import random
from dataclasses import replace

import numpy as np
from scipy.signal import fftconvolve
import pygame
import pygame_gui
from pygame_gui import UIManager
from pygame_gui.elements import (
    UIHorizontalSlider, UIButton, UITextEntryLine, UIDropDownMenu)

from schellingchords.chords import VOCABULARIES
from schellingchords.config import Config
from schellingchords.model import SchellingChordModel
from schellingchords.viz import LatticeView
from schellingchords.player import LivePlayer
from schellingchords.runtime import RuntimeParams
from schellingchords.sonify import chord_to_notes, CHORD_PITCH_CLASSES


class _DispatchingUIManager(UIManager):
    """UIManager whose ``process_events`` also routes slider-moved events.

    The GUI is driven by feeding events through the manager. The M9.T3 tests
    call ``manager.process_events([event])`` with a *list* holding a synthetic
    ``UI_HORIZONTAL_SLIDER_MOVED`` event, so this accepts either a single event
    or an iterable, forwards each to the base manager, then dispatches slider
    moves back to the owning app for immediate write-through.
    """

    def __init__(self, *args, app=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app

    def process_events(self, events):
        batch = events if isinstance(events, (list, tuple)) else [events]
        for event in batch:
            super().process_events(event)
            if self._app is None:
                continue
            etype = getattr(event, "type", None)
            if etype == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
                self._app._on_slider_moved(event)
            elif etype == pygame_gui.UI_BUTTON_PRESSED:
                # Route a real mouse click on a button to the callback bound as
                # element.click (the same callback the tests invoke directly).
                cb = getattr(getattr(event, "ui_element", None), "click", None)
                if callable(cb):
                    cb()
            elif etype == pygame_gui.UI_TEXT_ENTRY_FINISHED:
                self._app._on_seed_entered(event)
            elif etype == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                self._app._on_dropdown_changed(event)


class SchellingGUI:
    """Control panel embedding a ``LatticeView`` and a ``LivePlayer``."""

    WINDOW_SIZE = (1000, 800)
    # Params mirrored between the sliders, config files, and RuntimeParams.
    _CONFIG_FIELDS = (
        "n_chord_types", "bars_per_window", "vacancy_fraction", "tolerance",
        "happiness", "radius", "tempo_bpm", "seed", "vocabulary",
    )
    _DEFAULTS = dict(
        tolerance=0.5, happiness=0.5, vacancy_fraction=0.25, radius=2,
        tempo_bpm=120, n_chord_types=7, bars_per_window=4, seed=42, beats_per_bar=4,
        vocabulary="diatonic_major",
    )
    # Vocabulary key <-> human label for the dropdown.
    _VOCAB_LABELS = {"diatonic_major": "C major", "c_minor": "C minor"}
    # Scenario preset name -> the "no scenario chosen yet" sentinel is the first entry.
    _SCENARIO_OPTIONS = [
        "— scenario —", "Schelling",
        "Beethoven 5-2", "Beethoven 5-2 shuffled",
        "Beethoven 5-1", "Beethoven 5-1 shuffled"]
    # Note subdivision: slider level -> slots(beats) per 4/4 bar, and note-value name
    # + number of flags on the notehead stem.
    _SUBDIV_BPB = {1: 4, 2: 8, 3: 16}          # level -> beats_per_bar
    _BPB_LEVEL = {4: 1, 8: 2, 16: 3}
    _BPB_NAME = {4: "quarter", 8: "eighth", 16: "16th"}
    _BPB_FLAGS = {4: 0, 8: 1, 16: 2}
    _NOTE_RELEASE_MS = 300  # long release: previous voice rings out (doesn't hard-cut)
                            # so a sustain continues across transitions / window wrap
    _REARTICULATE_MS = 45   # min gap between re-attacks of a held/repeated chord
                            # (so each note gets a little attack, but fast runs
                            # don't turn back into a machine-gun buzz)
    _REVERB_WET = 0.30      # amount of reverb mixed under the dry tone
    _DRY_GAIN = 0.80        # dry-signal level in the mix
    _PAN_WIDTH = 0.90       # 0 = mono/centre, 1 = full hard-left..hard-right by slot

    def __init__(self, config=None):
        pygame.init()
        self.surface = pygame.display.set_mode(self.WINDOW_SIZE)
        self.manager = _DispatchingUIManager(self.WINDOW_SIZE, app=self)

        # Audio: numpy-synthesised chord tones through pygame.mixer (no external
        # synth needed). Guarded so headless/dummy-audio runs stay silent and safe.
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            self._mixer_ok = pygame.mixer.get_init() is not None
            if self._mixer_ok:
                pygame.mixer.set_num_channels(32)   # headroom for overlapping chord tails

        except Exception:
            self._mixer_ok = False
        self._sound_on = True
        self._spatial_on = True         # reverb + pan-by-position (tier-2 spatial audio)
        self._sound_cache = {}
        self._ir = None                 # cached stereo reverb impulse response

        cfg = config if config is not None else Config(
            n_chord_types=2, radius=1, seed=8675309, vacancy_fraction=0.2)
        self.config = cfg
        self.config_path = "config.json"
        # Explicit starting window for a scenario (e.g. Beethoven 5-2); None =>
        # the model places chords randomly. Applied on reset() when its length
        # matches the current window; a structural change that alters the window
        # length silently falls back to random placement. When _shuffle_initial is
        # set, reset() scatters this window's contents to random positions keyed on
        # the seed (same note/rest counts, randomised layout).
        self._initial_window = None
        self._shuffle_initial = False
        # slot index -> explicit MIDI voicing, for scenarios that voice a melody
        # (Beethoven). Empty => audio uses name-based (pitch-class) voicing.
        self._voicing_map = {}

        # Single RuntimeParams instance shared with the player: slider
        # write-through mutates exactly the object the player reads.
        self.runtime_params = RuntimeParams()
        self._seed_runtime_from_config(cfg)

        # A live Schelling model the player steps at each window boundary.
        self.model = SchellingChordModel(config=cfg)
        # Point the model's live params at the SAME object the sliders write to, so
        # tolerance/radius changes take effect on the next step (DESIGN §80-83).
        self.model.params = self.runtime_params
        self.live_player = LivePlayer(model=self.model, runtime_params=self.runtime_params)

        self._lattice_pos = (10, 470)          # where the strip is blitted in the window
        self._beat_accum = 0.0                 # seconds accumulated toward the next beat
        self._rebuild_lattice()

        # Text: dark ink labels rendered over the eggshell background.
        self._font = pygame.font.SysFont(None, 22)
        self._title_font = pygame.font.SysFont(None, 34, bold=True)
        self._ink = (40, 40, 46)

        self._build_controls()

    def _rebuild_lattice(self):
        """(Re)derive the colour map + LatticeView from the current model window.
        Called at init and on reset (when structural params change the window)."""
        # Colour index per chord = its FIXED position in the whole vocabulary, and the
        # palette is sized to the whole vocabulary — so a chord keeps the same colour
        # no matter how many chord types are present (n_chord_types, scenario, etc.).
        # LatticeView colours slot i by palette[idx] only for idx > 0, so index from 1.
        window = list(self.model.window)
        vocab_key = getattr(self.config, "vocabulary", "diatonic_major")
        vocab_names = [c.name for c in
                       VOCABULARIES.get(vocab_key, VOCABULARIES["diatonic_major"])()]
        self._chord_index = {name: i + 1 for i, name in enumerate(vocab_names)}
        # Any window chord outside the vocabulary (shouldn't normally happen) still
        # gets a distinct index so it colours rather than reading as a rest.
        for name in sorted({c for c in window if c is not None}):
            self._chord_index.setdefault(name, len(self._chord_index) + 1)
        self._active_chords = {c for c in window if c is not None}  # present => legend fill
        self.lattice_view = LatticeView(
            n_chord_types=len(self._chord_index) + 1,   # fixed palette size => fixed hues
            n_cells=len(window),
        )
        self.lattice_view.rest_colour = (222, 216, 201)  # light rests on the eggshell UI
        self._reset_stepper()

    # -- per-beat stepper (drives the REAL model; identical to headless) -------
    def _reset_stepper(self):
        """Live-view state. The current window (t) is shown up top; the next window
        (t+1) is precomputed by one real model.step() and revealed beat-by-beat in
        the ghost below as the playhead crosses each origin. At sweep end the ghost
        becomes the current window. Because it uses model.step(), the on-screen
        trajectory is exactly the headless trajectory for the same seed."""
        self._cur = list(self.model.window)      # current window (top staff)
        self._ghost = [None] * len(self._cur)    # next window, revealed as we sweep
        self._plan = None                        # full next window (lazy: computed on first beat)
        self._moves = {}                         # origin -> target for this transition
        self._ph = 0                             # playhead beat index over _cur
        self._window_index = 0
        self._playing = False
        self._paused = True
        self._beat_accum = 0.0
        self._unhappy_history = []                # count of unhappy chords per window
        self._chart_capacity = 32                 # windows across the chart; doubles at 95% full
        # Monophonic audio voice: the chord of the last slot the playhead sounded
        # (for onset detection) and the channel currently ringing (for note-off).
        self._voice_prev = None
        self._last_attack_ms = 0                   # wall-clock of the last note attack
        if getattr(self, "_voice_channel", None) is not None:
            try:
                self._voice_channel.stop()        # silence any ringing note on reset
            except Exception:
                pass
        self._voice_channel = None

    def _ensure_plan(self):
        """Compute the next window by stepping the real model (same call, same rng,
        same result as headless)."""
        if self._plan is None:
            self.model.step()
            self._plan = list(self.model.window)
            self._moves = dict(getattr(self.model, "last_moves", {}))
            self._unhappy_history.append(int(getattr(self.model, "last_unhappy", len(self._moves))))
            if len(self._unhappy_history) > 240:  # cap memory on long runs
                self._unhappy_history.pop(0)

    def _advance_beat(self):
        """Cross one beat: reveal that origin's decision into the ghost, advance the
        playhead, and roll the ghost up to current at the end of the window."""
        self._ensure_plan()
        name = self._cur[self._ph]
        if name is not None:                     # rests have no agent to reveal
            self._ghost[self._moves.get(self._ph, self._ph)] = name
        self._ph += 1
        if self._ph >= len(self._cur):
            self._cur = self._plan               # ghost scrolls up to become current
            self._ghost = [None] * len(self._cur)
            self._ph = 0
            self._window_index += 1
            self._plan = None                    # next sweep recomputes lazily
        # Sound the beat the playhead now sits on, so audio matches the rendered
        # playhead position (render() reads self._ph after this returns).
        self._play_beat(self._cur[self._ph], self._ph)

    def _on_run(self):
        self._playing, self._paused = True, False
        self.live_player.play()                  # keep frozen live_player state in sync
        self._play_beat(self._cur[self._ph], self._ph)  # sound the beat under the playhead now

    def _on_pause(self):
        self._playing, self._paused = False, True
        self.live_player.pause()

    def _on_quit(self):
        self._running = False

    def _on_reseed(self):
        """Pick a new random seed, reflect it in the seed input, and reset so the new
        starting arrangement takes effect (seed is a structural param)."""
        new_seed = random.randint(0, 9999)
        self.runtime_params.seed = new_seed
        self.seed_input.set_text(str(new_seed))
        self.reset()

    def _on_seed_entered(self, event):
        """Seed numeric input committed (Enter): apply it and reset."""
        if getattr(event, "ui_element", None) is not self.seed_input:
            return
        try:
            self.runtime_params.seed = int(event.text)
        except (ValueError, TypeError):
            return
        self.reset()

    def _on_dropdown_changed(self, event):
        """A dropdown selection changed: vocabulary switches the chord set (and
        clears any scenario seed); scenario applies a bundle of presets."""
        el = getattr(event, "ui_element", None)
        text = getattr(event, "text", None)
        if el is getattr(self, "vocab_dropdown", None):
            key = {v: k for k, v in self._VOCAB_LABELS.items()}.get(text, "diatonic_major")
            self.runtime_params.vocabulary = key
            self._initial_window = None      # a manual vocab pick is not a scenario
            self._shuffle_initial = False
            self._voicing_map = {}
            self.reset()
        elif el is getattr(self, "scenario_dropdown", None):
            self._apply_scenario(text)

    # -- scenario presets -----------------------------------------------------
    def _voiced(self, name, melody_midi):
        """Voice ``name`` as a triad with ``melody_midi`` as the top (melody) note
        and the remaining chord tones stacked just below it, so the audible top
        line follows the actual Beethoven melody. Returns a tuple of MIDI notes."""
        mel = int(melody_midi)
        mel_pc = mel % 12
        notes = [mel]
        for pc in CHORD_PITCH_CLASSES.get(name, []):
            if pc % 12 == mel_pc:
                continue
            notes.append(mel - ((mel - pc) % 12))   # nearest instance at/below mel
        return tuple(sorted(notes))

    def _beethoven_gesture_pairs(self, s_name, s_mel, l_name, l_mel):
        """One 16-slot bar of the motif rhythm as (chord_name, voicing) pairs, with
        the melody note voiced on top so the phrase's contour is audible:

            ·  ·   s s  ·  s s  ·  s s   ·   L L L L  ·
            eighth-rest │ 3 eighth-notes (2×16th each, split by a 16th rest) │
            a 16th rest │ the long note as 4×16th │ a trailing rest
        """
        S = (s_name, self._voiced(s_name, s_mel))
        L = (l_name, self._voiced(l_name, l_mel))
        R = (None, None)
        return [R, R, S, S, R, S, S, R, S, S, R, L, L, L, L, R]

    def _beethoven_pairs_5_2(self):
        """5-2: two phrases over 4 bars (64 slots) — phrase | fermata rest | phrase |
        fermata rest. Phrase 1 is the tonic G-G-G-E♭ (melody G→E♭, a major third
        down); phrase 2 is the dominant answer F-F-F-D voiced ``Bdim``→``G`` (melody
        F→D, a minor third down — about the same descent). Each phrase is followed by
        a bar of rest, the held-note fermata that the sustain audio rings through."""
        rest = [(None, None)] * 16
        return (self._beethoven_gesture_pairs("G", 67, "Eb", 63)
                + rest
                + self._beethoven_gesture_pairs("Bdim", 65, "G", 62)
                + rest)

    def _beethoven_pairs_5_1(self, factor=4):
        """5-1: phrase 1 (melody G→E♭) stretched ``factor``× (``factor`` bars), then a
        fermata rest bar — ``factor``+1 bars total. Played ``factor``× uptempo it
        sounds like 5-2's phrase 1 plus its held-note fermata, but hands the model
        ``factor``× the agents. The stretch keeps the descending melody voicing."""
        base = self._beethoven_gesture_pairs("G", 67, "Eb", 63)
        stretched = [p for p in base for _ in range(factor)]
        return stretched + [(None, None)] * 16          # fermata rest bar

    def _install_scenario_window(self, pairs, shuffled):
        """Set the initial window (chord names) and, for the faithful (non-shuffled)
        variant, the slot→voicing map that voices the melody. The shuffled variant
        moves chords off their slots, so it uses name-based (pitch-class) voicing."""
        self._initial_window = [name for name, _ in pairs]
        self._shuffle_initial = shuffled
        self._voicing_map = ({} if shuffled
                             else {i: v for i, (_, v) in enumerate(pairs) if v is not None})

    def _apply_scenario(self, name):
        """Preset a bundle of parameters for a named scenario, then rebuild."""
        rp = self.runtime_params
        if name == "Schelling":
            # uptempo, 16th notes, two maximally-distant C-major chords, random start
            self._initial_window = None
            self._shuffle_initial = False
            self._voicing_map = {}
            rp.vocabulary = "diatonic_major"
            rp.n_chord_types = 2
            rp.beats_per_bar = 16
            rp.bars_per_window = 2
            rp.tempo_bpm = 360
        elif name in ("Beethoven 5-2", "Beethoven 5-2 shuffled"):
            # both phrases in C minor, 16th notes, 4 bars (phrase|rest|phrase|rest);
            # the "shuffled" variant scatters the notes/rests by seed.
            rp.vocabulary = "c_minor"
            rp.n_chord_types = 2
            rp.beats_per_bar = 16
            rp.bars_per_window = 4          # phrase | fermata rest | phrase | fermata rest
            rp.tempo_bpm = 70               # 5-2 reads best slow
            self._install_scenario_window(self._beethoven_pairs_5_2(), name.endswith("shuffled"))
        elif name in ("Beethoven 5-1", "Beethoven 5-1 shuffled"):
            # phrase 1 stretched 4× (4 bars) + a fermata rest bar = 5 bars, played 4×
            # uptempo (280 = 4×70): sounds like 5-2's phrase 1 + fermata, 4× the agents.
            rp.vocabulary = "c_minor"
            rp.n_chord_types = 2
            rp.beats_per_bar = 16
            rp.bars_per_window = 5          # phrase (×4 = 4 bars) + fermata rest bar
            rp.tempo_bpm = 280
            self._install_scenario_window(self._beethoven_pairs_5_1(4), name.endswith("shuffled"))
        else:
            return                            # the "— scenario —" sentinel: no-op
        self._sync_controls_from_params()
        self.reset()

    def _sync_controls_from_params(self):
        """Push runtime-param values a scenario just set back onto the widgets that
        mirror them, so the sliders/dropdowns show the applied preset."""
        rp = self.runtime_params
        self.tempo_slider.set_current_value(rp.tempo_bpm)
        self.n_chord_types_slider.set_current_value(rp.n_chord_types)
        self.bars_per_window_slider.set_current_value(rp.bars_per_window)
        self.subdiv_slider.set_current_value(self._BPB_LEVEL.get(int(rp.beats_per_bar), 1))
        try:                                  # dropdown text is best-effort
            self.vocab_dropdown.selected_option = self._VOCAB_LABELS[rp.vocabulary]
        except Exception:
            pass

    def _on_toggle_sound(self):
        self._sound_on = not self._sound_on
        self.sound_button.set_text("Sound: On" if self._sound_on else "Sound: Off")

    def _on_toggle_spatial(self):
        self._spatial_on = not self._spatial_on
        self.spatial_button.set_text("Spatial: On" if self._spatial_on else "Spatial: Off")

    def _reverb_ir(self, freq):
        """Cached stereo reverb impulse response: two independent (decorrelated)
        decaying-noise tails, giving the note a diffuse sense of space/width. Built
        once and reused for every chord."""
        if self._ir is None:
            length = int(freq * 0.9)                 # ~0.9 s tail
            t = np.arange(length, dtype=np.float64) / freq
            decay = np.exp(-t / 0.28)
            rng = np.random.default_rng(1234)
            pre = int(freq * 0.02)                   # 20 ms pre-delay
            def tail():
                ir = rng.standard_normal(length) * decay
                ir[:pre] = 0.0
                energy = float(np.sqrt(np.sum(ir * ir))) or 1.0
                return ir / energy                   # unit energy => stable wet level
            self._ir = (tail(), tail())
        return self._ir

    def _make_chord_sound(self, notes, spatial=True):
        """Synthesise a chord tone from an explicit list of MIDI ``notes`` (additive
        sines with a couple of harmonics), as a cached pygame Sound. The envelope is
        a quick attack then a natural exponential decay to silence over ~1.5 s, so a
        note rings for its duration and then releases on its own — long enough that a
        clump of identical slots reads as one held note (not a 16th blip), but not an
        endless sustain. The note is also cut at the next onset by the channel
        fadeout in ``_play_beat``."""
        freq, _size, channels = pygame.mixer.get_init()
        dur = 1.5                                       # capped; note-off may cut sooner
        n = int(freq * dur)
        t = np.arange(n, dtype=np.float64) / freq
        wave = np.zeros(n, dtype=np.float64)
        for pitch in notes:
            f = 440.0 * 2.0 ** ((int(pitch) - 69) / 12.0)
            # fundamental + soft 2nd/3rd harmonics for a reedy/organ tone (not a
            # pure sine, not a fast-decaying pluck).
            wave += (np.sin(2 * np.pi * f * t)
                     + 0.4 * np.sin(2 * np.pi * 2 * f * t)
                     + 0.2 * np.sin(2 * np.pi * 3 * f * t))
        # Envelope: 8 ms attack, then exp decay (~0.7 s time constant) so the note
        # holds audibly then fades to silence; a short end-fade guarantees zero at
        # the tail. Per-note release at onset boundaries is the channel fadeout.
        env = np.exp(-t / 0.7)
        a = min(int(freq * 0.008), n)                   # 8 ms attack
        if a:
            env[:a] *= np.linspace(0.0, 1.0, a)
        d = min(int(freq * 0.03), n)                    # 30 ms end-fade to zero
        if d:
            env[-d:] *= np.linspace(1.0, 0.0, d)
        wave *= env
        peak = float(np.max(np.abs(wave))) or 1.0
        dry = wave / peak
        if spatial and channels == 2:
            # Convolve the dry tone with the stereo reverb IR and mix under it. The
            # dry signal is identical L/R (centred); the wet tails are decorrelated,
            # giving diffuse width/space. Slot-based panning is applied at playback
            # in _play_beat via the channel's stereo volume.
            irl, irr = self._reverb_ir(freq)
            wet_l = fftconvolve(dry, irl)
            wet_r = fftconvolve(dry, irr)
            m = len(wet_l)
            out_l = np.zeros(m, dtype=np.float64)
            out_r = np.zeros(m, dtype=np.float64)
            out_l[:len(dry)] += dry * self._DRY_GAIN
            out_r[:len(dry)] += dry * self._DRY_GAIN
            out_l += wet_l * self._REVERB_WET
            out_r += wet_r * self._REVERB_WET
            pk = max(float(np.max(np.abs(out_l))), float(np.max(np.abs(out_r)))) or 1.0
            # 0.30 leaves headroom for several ringing/overlapping tails (long release).
            left = (out_l / pk * 0.30 * 32767).astype(np.int16)
            right = (out_r / pk * 0.30 * 32767).astype(np.int16)
            arr = np.column_stack([left, right])
        else:
            # Dry (spatial off, or mono mixer): centre the tone, no reverb.
            mono = (dry * 0.30 * 32767).astype(np.int16)
            arr = np.column_stack([mono, mono]) if channels == 2 else mono
        return pygame.sndarray.make_sound(np.ascontiguousarray(arr))

    def _play_beat(self, name, slot=None):
        """Sound the slot under the playhead. Every note gets a little attack, but a
        run of the same chord only re-attacks every ``_REARTICULATE_MS`` — so a block
        of identical slots is re-articulated (it doesn't fade out before the last
        note) yet a fast run doesn't turn into a machine-gun. A rest lets the current
        note ring on. The previous voice is released with a long fade
        (``_NOTE_RELEASE_MS``) rather than a hard cut, so its (panned) tail rings out
        and the sustain continues across transitions and the window wrap."""
        prev = self._voice_prev
        self._voice_prev = name
        if not (self._sound_on and self._mixer_ok) or name is None:
            return                          # muted or a rest: the current note rings on
        now = pygame.time.get_ticks()
        if name == prev and (now - self._last_attack_ms) < self._REARTICULATE_MS:
            return                          # same chord, too soon to re-strike: ring on
        self._last_attack_ms = now
        try:
            # Scenario melody voicing for this slot, if any; else pitch-class voicing.
            voicing = self._voicing_map.get(slot) if slot is not None else None
            notes = tuple(voicing) if voicing else tuple(int(p) for p in chord_to_notes(name))
            spatial = self._spatial_on
            key = (notes, spatial)                  # dry and spatial samples cache apart
            snd = self._sound_cache.get(key)
            if snd is None:
                snd = self._sound_cache[key] = self._make_chord_sound(notes, spatial)
            ch = self._voice_channel
            if ch is not None and ch.get_busy():
                ch.fadeout(self._NOTE_RELEASE_MS)   # long release: previous tail rings out
            new_ch = snd.play()
            if new_ch is not None and spatial:
                # Pan by lattice position: slot 0 -> left, last slot -> right, so
                # as like-chords cluster you hear them group in the stereo field.
                n_cells = len(self._cur) if getattr(self, "_cur", None) else 1
                pos = 0.5 if slot is None else slot / max(1, n_cells - 1)
                eff = 0.5 + (pos - 0.5) * self._PAN_WIDTH        # equal-power pan
                new_ch.set_volume(float(np.cos(eff * np.pi / 2)),
                                  float(np.sin(eff * np.pi / 2)))
            self._voice_channel = new_ch
        except Exception:
            self._voice_channel = None      # never let audio break the loop

    def _on_step(self):
        self._advance_beat()
        # Keep the frozen live_player's playhead in step without letting its own
        # boundary logic fire a second model.step() and desync the view.
        self.live_player.playhead += 1

    def reset(self):
        """Reset button: apply STRUCTURAL params (n_chord_types, bars_per_window,
        vacancy_fraction, seed) by rebuilding the model, then rewind. Runtime params
        (tolerance/happiness/tempo) already take effect live and are preserved via the
        shared RuntimeParams object."""
        rp = self.runtime_params
        # Commit whatever is currently typed in the seed field, even if the user
        # never pressed Enter — otherwise Reset would rebuild with the old seed.
        if hasattr(self, "seed_input"):
            try:
                rp.seed = int(self.seed_input.get_text())
            except (ValueError, TypeError):
                pass
        cfg = replace(
            self.config,
            n_chord_types=max(2, min(7, int(rp.n_chord_types))),   # vocabulary is 7 triads
            bars_per_window=max(1, int(rp.bars_per_window)),
            beats_per_bar=int(getattr(rp, "beats_per_bar", 4)),    # note subdivision
            vacancy_fraction=min(0.95, max(0.0, float(rp.vacancy_fraction))),
            seed=int(rp.seed),
            vocabulary=getattr(rp, "vocabulary", self.config.vocabulary),
        )
        self.config = cfg
        # Use the scenario's explicit starting window only when it fits the current
        # window length; otherwise fall back to random placement. In shuffle mode,
        # scatter the same contents to random positions keyed on the seed, so the
        # note/rest counts are preserved but the layout re-randomises with the seed.
        win_len = cfg.bars_per_window * cfg.beats_per_bar
        init = None
        if self._initial_window is not None and len(self._initial_window) == win_len:
            init = list(self._initial_window)
            if self._shuffle_initial:
                random.Random(cfg.seed).shuffle(init)
        self.model = SchellingChordModel(config=cfg, initial_window=init)
        self.model.params = self.runtime_params   # live tolerance/radius (see __init__)
        self.live_player = LivePlayer(model=self.model, runtime_params=self.runtime_params)
        self._rebuild_lattice()
        self._beat_accum = 0.0

    # -- construction helpers -------------------------------------------------
    def _seed_runtime_from_config(self, config):
        for name, default in self._DEFAULTS.items():
            setattr(self.runtime_params, name, getattr(config, name, default))

    def _slider(self, pos, start, value_range, click_increment=1):
        return UIHorizontalSlider(
            relative_rect=pygame.Rect(pos, (200, 30)),
            start_value=start,
            value_range=value_range,
            click_increment=click_increment,   # step size for the +/- arrow buttons
            manager=self.manager,
        )

    def _button(self, pos, text, callback):
        btn = UIButton(
            relative_rect=pygame.Rect(pos, (100, 30)),
            text=text,
            manager=self.manager,
        )
        # Expose a headless-friendly click() that runs the bound action.
        btn.click = callback
        return btn

    def _build_controls(self):
        rp = self.runtime_params
        self.tolerance_slider = self._slider((10, 10), rp.tolerance, (0.0, 1.0), click_increment=0.1)
        self.vacancy_slider = self._slider((10, 50), rp.vacancy_fraction, (0.0, 1.0), click_increment=0.1)
        self.tempo_slider = self._slider((10, 90), rp.tempo_bpm, (40, 480))
        self.n_chord_types_slider = self._slider((10, 130), rp.n_chord_types, (2, 7))
        self.bars_per_window_slider = self._slider((10, 170), rp.bars_per_window, (1, 8))
        self.radius_slider = self._slider((10, 210), rp.radius, (1, 6))
        # note subdivision: level 1/2/3 -> quarter/eighth/16th (applied on reset)
        self.subdiv_slider = self._slider(
            (10, 250), self._BPB_LEVEL.get(int(getattr(rp, "beats_per_bar", 4)), 1), (1, 3))

        # seed is a numeric text input (digits only), not a slider.
        self.seed_input = UITextEntryLine(
            relative_rect=pygame.Rect((10, 290), (100, 30)), manager=self.manager)
        self.seed_input.set_allowed_characters("numbers")
        self.seed_input.set_text(str(int(rp.seed)))

        self.run_button = self._button((10, 350), "Run", self._on_run)
        self.pause_button = self._button((120, 350), "Pause", self._on_pause)
        self.step_button = self._button((230, 350), "Step", self._on_step)
        self.reset_button = self._button((340, 350), "Reset", self.reset)
        self.sound_button = self._button((450, 350), "Sound: On", self._on_toggle_sound)
        self.load_button = self._button((10, 390), "Load", self.load_config)
        self.save_button = self._button((120, 390), "Save", self.save_config)
        self.reseed_button = self._button((230, 390), "re-seed", self._on_reseed)
        self.quit_button = self._button((340, 390), "Quit", self._on_quit)
        self.spatial_button = self._button((450, 390), "Spatial: On", self._on_toggle_spatial)

        # Scenario preset + chord-vocabulary dropdowns (right column, below chart).
        self.scenario_dropdown = UIDropDownMenu(
            options_list=list(self._SCENARIO_OPTIONS),
            starting_option=self._SCENARIO_OPTIONS[0],
            relative_rect=pygame.Rect((560, 355), (200, 30)),
            manager=self.manager,
        )
        self.vocab_dropdown = UIDropDownMenu(
            options_list=list(self._VOCAB_LABELS.values()),
            starting_option=self._VOCAB_LABELS.get(
                getattr(rp, "vocabulary", "diatonic_major"), "C major"),
            relative_rect=pygame.Rect((820, 355), (150, 30)),
            manager=self.manager,
        )

        # (display name, slider, y) — drawn as "name: value" text right of each slider.
        self._slider_labels = [
            ("tolerance", self.tolerance_slider, 10),
            ("vacancy", self.vacancy_slider, 50),
            ("tempo", self.tempo_slider, 90),
            ("n_types", self.n_chord_types_slider, 130),
            ("bars/win", self.bars_per_window_slider, 170),
            ("radius", self.radius_slider, 210),
        ]

    # -- event handling -------------------------------------------------------
    def _on_slider_moved(self, event):
        slider = getattr(event, "ui_element", None)
        value = getattr(event, "value", None)
        if slider is None or value is None:
            return
        rp = self.runtime_params
        if slider is self.tolerance_slider:
            value = round(float(value) * 10) / 10   # snap to 0.1 increments
            slider.set_current_value(value)
            rp.tolerance = float(value)
        elif slider is self.vacancy_slider:
            value = round(float(value) * 10) / 10   # snap to 0.1 increments
            slider.set_current_value(value)
            rp.vacancy_fraction = float(value)
        elif slider is self.tempo_slider:
            rp.tempo_bpm = int(value)
        elif slider is self.n_chord_types_slider:
            rp.n_chord_types = int(value)
        elif slider is self.bars_per_window_slider:
            rp.bars_per_window = int(value)
        elif slider is self.radius_slider:
            rp.radius = int(value)
        elif slider is self.subdiv_slider:      # structural: applied on reset
            rp.beats_per_bar = self._SUBDIV_BPB.get(int(round(value)), 4)

    # -- config load / save ---------------------------------------------------
    def save_config(self):
        data = {f: getattr(self.runtime_params, f, None) for f in self._CONFIG_FIELDS}
        with open(self.config_path, "w") as fh:
            json.dump(data, fh)

    def load_config(self):
        if not os.path.exists(self.config_path):
            return
        with open(self.config_path) as fh:
            data = json.load(fh)
        for f in self._CONFIG_FIELDS:
            if f in data:
                setattr(self.runtime_params, f, data[f])

    # -- frame loop -----------------------------------------------------------
    def update(self, dt):
        self.manager.update(dt)
        # Beat clock: while playing, cross beats at tempo. Guard caps catch-up so a
        # large dt (after a stall) can't spiral.
        if self._playing and not self._paused:
            bpm = max(1, int(getattr(self.runtime_params, "tempo_bpm", 120)))
            bpb = max(1, int(getattr(self.config, "beats_per_bar", 4)))
            # each slot is a 1/bpb-of-a-4/4-bar note; tempo is quarter-note BPM.
            slot_dur = (60.0 / bpm) * (4.0 / bpb)
            self._beat_accum += dt
            guard = 0
            while self._beat_accum >= slot_dur and guard < 64:
                self._advance_beat()
                self._beat_accum -= slot_dur
                guard += 1

    _BG = (240, 234, 214)  # eggshell
    # Natural pitch class -> diatonic letter index (C=0..B=6). C-major triads only,
    # so every note is natural and needs no accidental/ledger handling.
    _PC_TO_LETTER = {0: 0, 2: 1, 4: 2, 5: 3, 7: 4, 9: 5, 11: 6}
    _BASS_BOTTOM_STEP = 18  # G2 = bass-clef bottom line, our vertical reference
    _STAFF_H = 84
    _STAFF_GAP = 72   # room between staves for the top caption + the ghost's up-stems

    def render(self):
        self.surface.fill(self._BG)
        lx, ly = self._lattice_pos
        w = self.WINDOW_SIZE[0] - lx - 15   # stretch the bars to (nearly) full window width
        # Current window (t) with the decision playhead; next window (t+1) ghost below.
        self._draw_staff(self._cur, lx, ly, w, self._STAFF_H, ghost=False, playhead=self._ph)
        self._draw_staff(self._ghost, lx, ly + self._STAFF_H + self._STAFF_GAP, w,
                         self._STAFF_H, ghost=True, playhead=None)
        self._draw_chart(480, 40, 505, 300)
        self.manager.draw_ui(self.surface)   # controls last
        self._draw_text_overlay()

    def _draw_chart(self, x0, y0, w, h):
        """Live line chart of the number of unhappy chords per window."""
        surf = self.surface
        hist = self._unhappy_history
        pygame.draw.rect(surf, (250, 249, 244), (x0, y0, w, h))         # paper panel
        pygame.draw.rect(surf, (200, 196, 182), (x0, y0, w, h), 1)      # border
        surf.blit(self._font.render("Unhappy chords over time", True, self._ink), (x0 + 8, y0 + 6))
        left, top = x0 + 34, y0 + 30
        pw, ph = w - 34 - 12, h - 30 - 28
        occ = sum(1 for c in self._cur if c is not None) or 1
        ymax = max(occ, max(hist) if hist else 1)
        axis = (150, 146, 134)
        pygame.draw.line(surf, axis, (left, top), (left, top + ph), 1)           # y axis
        pygame.draw.line(surf, axis, (left, top + ph), (left + pw, top + ph), 1)  # x axis
        surf.blit(self._font.render(str(int(ymax)), True, self._ink), (x0 + 6, top - 9))
        surf.blit(self._font.render("0", True, self._ink), (x0 + 6, top + ph - 9))
        surf.blit(self._font.render("window →", True, self._ink), (left + pw - 62, top + ph + 8))
        n = len(hist)
        if n >= 1:
            # Advance at a fixed windows-per-pixel; when the line passes 95% of the
            # width, double the capacity so the x-axis compresses and the line has
            # room to keep advancing rightward.
            while n - 1 > 0.95 * self._chart_capacity:
                self._chart_capacity *= 2
            cap = self._chart_capacity
            def _x(i): return left + pw * (i / cap)
            def _y(v): return top + ph - ph * v / ymax
            if n >= 2:
                pygame.draw.lines(surf, (200, 20, 40), False,
                                  [(_x(i), _y(v)) for i, v in enumerate(hist)], 2)
            else:
                pygame.draw.circle(surf, (200, 20, 40), (int(_x(0)), int(_y(hist[0]))), 3)
        if hist:
            surf.blit(self._font.render(f"now: {hist[-1]}", True, self._ink), (x0 + w - 92, y0 + 6))

    def _staff_step(self, midi):
        """Diatonic staff step of a natural MIDI note (higher = higher on the staff)."""
        letter = self._PC_TO_LETTER.get(midi % 12, 0)
        octave = midi // 12 - 1
        return octave * 7 + letter

    def _draw_staff(self, window, x0, y0, w, h, ghost=False, playhead=None):
        """Draw one window as a bass staff: faint chord-colour columns, 5 staff
        lines, barlines every bar, noteheads (hollow if ghost), optional playhead."""
        surf = self.surface
        window = window or []
        n = max(1, len(window))
        cw = w / n
        beats_per_bar = int(getattr(self.config, "beats_per_bar", 4))

        line_spacing = 14
        half = line_spacing / 2.0
        staff_h = 4 * line_spacing
        bottom_y = int(y0 + h / 2 + staff_h / 2)

        pygame.draw.rect(surf, (250, 249, 244), (x0, y0, w, h))  # paper
        for i, name in enumerate(window):
            if name is None:
                continue
            colour = self.lattice_view.palette.get(self._chord_index.get(name, 0), self._ink)
            tint = tuple(int(c * 0.30 + 255 * 0.70) for c in colour)
            pygame.draw.rect(surf, tint, (int(x0 + i * cw), y0, int(cw) + 1, h))
        for k in range(5):
            yy = bottom_y - k * line_spacing
            pygame.draw.line(surf, (70, 70, 78), (x0, yy), (x0 + w, yy), 1)
        for b in range(0, n + 1, beats_per_bar):
            bx = int(x0 + b * cw)
            pygame.draw.line(surf, (30, 30, 36), (bx, bottom_y - staff_h - half), (bx, bottom_y + half), 2)
        nflags = self._BPB_FLAGS.get(beats_per_bar, 0)   # 0/1/2 for quarter/eighth/16th
        for i, name in enumerate(window):
            if name is None:
                continue
            cx = x0 + i * cw + cw / 2.0
            colour = self.lattice_view.palette.get(self._chord_index.get(name, 0), self._ink)
            rx, ry = max(3.5, cw * 0.30), half * 0.95
            ys = []
            for midi in chord_to_notes(name):
                ny = bottom_y - (self._staff_step(midi) - self._BASS_BOTTOM_STEP) * half
                ys.append(ny)
                rect = (cx - rx, ny - ry, rx * 2, ry * 2)
                if ghost:
                    pygame.draw.ellipse(surf, colour, rect, 2)   # hollow = ghost
                else:
                    pygame.draw.ellipse(surf, colour, rect)
                    pygame.draw.ellipse(surf, (30, 30, 36), rect, 1)
            # stem UP the right side, plus a flag per subdivision (eighth/16th). The
            # captions sit BELOW each staff, so there is clear buffer above for stems.
            ink = colour if ghost else (30, 30, 36)
            sx = cx + rx
            stem_top = min(ys) - 2.4 * line_spacing
            pygame.draw.line(surf, ink, (sx, max(ys)), (sx, stem_top), 2)
            for f in range(nflags):
                fy = stem_top + f * 6
                pygame.draw.line(surf, ink, (sx, fy), (sx + 7, fy + 9), 2)
        if playhead is not None:
            px = int(x0 + (playhead % n) * cw + cw / 2.0)
            pygame.draw.line(surf, (200, 20, 40), (px, y0), (px, y0 + h), 3)

    def _draw_text_overlay(self):
        """Title, slider name/value labels, staff captions, and the colour legend."""
        lx, ly = self._lattice_pos
        # App title, top-right above the chart panel.
        self.surface.blit(self._title_font.render("SchellingChords", True, self._ink), (480, 8))
        for name, slider, y in self._slider_labels:
            txt = f"{name}: {slider.get_current_value():g}"
            self.surface.blit(self._font.render(txt, True, self._ink), (225, y + 7))
        # subdivision label (word) — reads the pending slider level, applied on reset
        bpb = self._SUBDIV_BPB.get(int(round(self.subdiv_slider.get_current_value())), 4)
        self.surface.blit(self._font.render(
            f"note: {self._BPB_NAME.get(bpb, '?')}", True, self._ink), (225, 257))
        # label for the seed numeric input (sits at y=290, to its right)
        self.surface.blit(self._font.render("seed", True, self._ink), (120, 297))
        # dropdown labels (right column, above each menu)
        self.surface.blit(self._font.render("scenario", True, self._ink), (560, 337))
        self.surface.blit(self._font.render("vocabulary", True, self._ink), (820, 337))
        # Captions sit BELOW each staff (leaving buffer above for the up-stems).
        self.surface.blit(self._font.render(
            "Current window (t) — a chord makes its move as the red playhead crosses it",
            True, self._ink), (lx, ly + self._STAFF_H + 5))
        self.surface.blit(self._font.render(
            "Next window (t+1) ghost — unhappy chords appear at a new slot; scrolls up when full",
            True, self._ink), (lx, ly + 2 * self._STAFF_H + self._STAFF_GAP + 5))
        # Colour legend: the ENTIRE active vocabulary, in vocab order. Chords present
        # in the current window are filled with their live colour; the rest are drawn
        # as an outline (inactive) and greyed — so the full palette is always visible
        # regardless of scenario, n_chord_types, or which chords happen to be present.
        x = lx
        y = ly + 2 * self._STAFF_H + self._STAFF_GAP + 28
        vocab_key = getattr(self.config, "vocabulary", "diatonic_major")
        vocab = VOCABULARIES.get(vocab_key, VOCABULARIES["diatonic_major"])()
        for chord in vocab:
            nm = chord.name
            if nm in self._active_chords:                # present in the current window
                colour = self.lattice_view.palette.get(self._chord_index[nm], self._ink)
                pygame.draw.rect(self.surface, colour, (x, y, 18, 18))
                label_col = self._ink
            else:                                        # inactive: outline + greyed label
                pygame.draw.rect(self.surface, (190, 186, 172), (x, y, 18, 18), 1)
                label_col = (170, 166, 156)
            self.surface.blit(self._font.render(nm, True, label_col), (x + 24, y))
            x += 24 + self._font.size(nm)[0] + 24

    def launch(self):
        clock = pygame.time.Clock()
        self._running = True
        while self._running:
            dt = clock.tick(60) / 1000.0
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:      # window close
                    self._running = False
            self.manager.process_events(events)    # Quit button sets _running=False
            self.update(dt)
            self.render()
            pygame.display.flip()
        pygame.quit()


if __name__ == "__main__":
    SchellingGUI().launch()
