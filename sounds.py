"""
sounds.py  —  Wandering in the Woods
Generates all sounds programmatically using numpy + pygame.
No external sound files needed. Works on Windows, Mac, Linux.

Usage in any mode file:
    from sounds import play_step, play_celebration, play_start, play_menu
"""

import pygame
import numpy as np

# ── sample rate ───────────────────────────────────────────────────────────────
SR = 44100   # samples per second

def _init():
    """Make sure mixer is ready."""
    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=SR, size=-16, channels=2, buffer=512)

def _sine(freq, duration_ms, volume=0.25, fade_ms=30):
    """
    Generate a stereo sine-wave Sound object.
    freq        : pitch in Hz
    duration_ms : length in milliseconds
    volume      : 0.0 – 1.0
    fade_ms     : fade-out length to avoid clicks
    """
    _init()
    n      = int(SR * duration_ms / 1000)
    t      = np.linspace(0, duration_ms / 1000, n, endpoint=False)
    wave   = np.sin(2 * np.pi * freq * t)

    # apply fade-out to remove click
    fade_n = min(int(SR * fade_ms / 1000), n)
    wave[-fade_n:] *= np.linspace(1, 0, fade_n)

    samples = (wave * volume * 32767).astype(np.int16)
    stereo  = np.column_stack([samples, samples])   # left + right
    return pygame.sndarray.make_sound(stereo)


# ── public sound functions ────────────────────────────────────────────────────

def play_step():
    """Short soft click played on every character move."""
    try:
        _sine(380, 55, volume=0.12).play()
    except Exception:
        pass


def play_start():
    """Two rising notes when the simulation starts."""
    try:
        _sine(440, 140).play()
        pygame.time.delay(150)
        _sine(550, 140).play()
    except Exception:
        pass


def play_celebration():
    """Ascending 4-note jingle when characters meet."""
    try:
        notes = [(523, 0), (659, 130), (784, 260), (1047, 390)]
        sounds = [(_sine(f, 200, volume=0.35), d) for f, d in notes]
        for snd, delay in sounds:
            pygame.time.delay(delay if delay == 0 else 130)
            snd.play()
    except Exception:
        pass


def play_menu():
    """Soft chime when the main menu appears."""
    try:
        _sine(660, 180, volume=0.2).play()
        pygame.time.delay(190)
        _sine(880, 180, volume=0.2).play()
    except Exception:
        pass


# ── optional TTS ──────────────────────────────────────────────────────────────

def speak(text):
    """
    Speak text aloud using pyttsx3 if installed.
    Silently skipped if pyttsx3 is not available.
    """
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", 150)
        engine.say(text)
        engine.runAndWait()
    except Exception:
        pass   # no TTS available — that is fine
