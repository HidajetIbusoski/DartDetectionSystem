"""
Sound effects manager for OfflineDarts.
Generates and plays synthesized sounds — no external audio files needed.
Uses QMediaPlayer for playback with WAV files generated via numpy.
"""

import numpy as np
import struct
import wave
import io
import os
import logging
from pathlib import Path
from enum import Enum

from PyQt6.QtCore import QUrl, QObject
from PyQt6.QtMultimedia import QSoundEffect

from config import ASSETS_DIR

logger = logging.getLogger(__name__)

SOUNDS_DIR = ASSETS_DIR / "sounds"
SOUNDS_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_RATE = 44100


class SoundType(Enum):
    """Available sound effects."""
    DART_HIT = "dart_hit"
    DART_DOUBLE = "dart_double"
    DART_TRIPLE = "dart_triple"
    DART_BULL = "dart_bull"
    DART_MISS = "dart_miss"
    BUST = "bust"
    CHECKOUT = "checkout"
    TURN_COMPLETE = "turn_complete"
    GAME_OVER = "game_over"
    ONE_EIGHTY = "one_eighty"


def _generate_sine(freq: float, duration: float, volume: float = 0.5,
                   fade_out: float = 0.1) -> np.ndarray:
    """Generate a sine wave tone."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    tone = np.sin(2 * np.pi * freq * t) * volume

    # Apply fade out
    fade_samples = int(SAMPLE_RATE * fade_out)
    if fade_samples > 0 and fade_samples < len(tone):
        fade = np.linspace(1.0, 0.0, fade_samples)
        tone[-fade_samples:] *= fade

    return tone


def _generate_noise(duration: float, volume: float = 0.3) -> np.ndarray:
    """Generate white noise burst."""
    samples = int(SAMPLE_RATE * duration)
    noise = np.random.uniform(-1, 1, samples) * volume
    # Quick fade out
    fade = int(samples * 0.7)
    if fade > 0:
        noise[-fade:] *= np.linspace(1.0, 0.0, fade)
    return noise


def _mix(*signals) -> np.ndarray:
    """Mix multiple audio signals together."""
    max_len = max(len(s) for s in signals)
    result = np.zeros(max_len)
    for s in signals:
        result[:len(s)] += s
    # Normalize
    peak = np.max(np.abs(result))
    if peak > 0:
        result = result / peak * 0.85
    return result


def _save_wav(filepath: str, data: np.ndarray):
    """Save numpy array as a WAV file."""
    # Convert to 16-bit PCM
    audio_16 = np.int16(data * 32767)
    with wave.open(filepath, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_16.tobytes())


def _generate_all_sounds():
    """Generate all sound effect WAV files."""
    sounds = {}

    # Dart hit — short thud (low freq noise + tone)
    hit_tone = _generate_sine(180, 0.08, 0.4, fade_out=0.06)
    hit_noise = _generate_noise(0.04, 0.5)
    sounds[SoundType.DART_HIT] = _mix(hit_tone, hit_noise)

    # Double — satisfying ping
    d1 = _generate_sine(880, 0.12, 0.5, fade_out=0.1)
    d2 = _generate_sine(1320, 0.08, 0.3, fade_out=0.06)
    sounds[SoundType.DART_DOUBLE] = _mix(d1, d2)

    # Triple — higher ping with harmonic
    t1 = _generate_sine(1100, 0.15, 0.5, fade_out=0.12)
    t2 = _generate_sine(1650, 0.1, 0.3, fade_out=0.08)
    t3 = _generate_sine(2200, 0.06, 0.15, fade_out=0.04)
    sounds[SoundType.DART_TRIPLE] = _mix(t1, t2, t3)

    # Bullseye — deep resonant hit
    b1 = _generate_sine(440, 0.2, 0.6, fade_out=0.15)
    b2 = _generate_sine(880, 0.15, 0.3, fade_out=0.1)
    b3 = _generate_sine(220, 0.25, 0.4, fade_out=0.2)
    sounds[SoundType.DART_BULL] = _mix(b1, b2, b3)

    # Miss — dull thud
    m1 = _generate_sine(100, 0.06, 0.3, fade_out=0.05)
    m2 = _generate_noise(0.03, 0.2)
    sounds[SoundType.DART_MISS] = _mix(m1, m2)

    # Bust — descending tone (disappointing)
    bust_len = 0.4
    t = np.linspace(0, bust_len, int(SAMPLE_RATE * bust_len), False)
    freq_sweep = np.linspace(600, 200, len(t))
    bust = np.sin(2 * np.pi * freq_sweep * t / SAMPLE_RATE * np.cumsum(np.ones_like(t) / SAMPLE_RATE)) * 0.4
    # Simple implementation
    bust = np.sin(2 * np.pi * np.cumsum(freq_sweep / SAMPLE_RATE)) * 0.4
    fade = np.linspace(1.0, 0.0, len(bust))
    bust *= fade
    sounds[SoundType.BUST] = bust

    # Checkout — ascending celebratory tones
    c1 = _generate_sine(523, 0.12, 0.5, fade_out=0.05)  # C5
    c2 = _generate_sine(659, 0.12, 0.5, fade_out=0.05)  # E5
    c3 = _generate_sine(784, 0.2, 0.6, fade_out=0.15)   # G5
    gap = np.zeros(int(SAMPLE_RATE * 0.05))
    sounds[SoundType.CHECKOUT] = np.concatenate([c1, gap, c2, gap, c3])

    # Turn complete — subtle click
    tc = _generate_sine(600, 0.05, 0.3, fade_out=0.04)
    sounds[SoundType.TURN_COMPLETE] = tc

    # Game over — grand fanfare
    go1 = _generate_sine(523, 0.15, 0.5, fade_out=0.05)
    go2 = _generate_sine(659, 0.15, 0.5, fade_out=0.05)
    go3 = _generate_sine(784, 0.15, 0.5, fade_out=0.05)
    go4 = _generate_sine(1047, 0.4, 0.6, fade_out=0.3)
    gap2 = np.zeros(int(SAMPLE_RATE * 0.03))
    sounds[SoundType.GAME_OVER] = np.concatenate([go1, gap2, go2, gap2, go3, gap2, go4])

    # 180! — dramatic ascending with harmonics
    e1 = _generate_sine(440, 0.1, 0.5, fade_out=0.04)
    e2 = _generate_sine(554, 0.1, 0.5, fade_out=0.04)
    e3 = _generate_sine(659, 0.1, 0.5, fade_out=0.04)
    e4 = _generate_sine(880, 0.3, 0.6, fade_out=0.25)
    e4h = _generate_sine(1760, 0.2, 0.2, fade_out=0.15)
    final = np.zeros(max(len(e4), len(e4h)))
    final[:len(e4)] += e4
    final[:len(e4h)] += e4h
    peak = np.max(np.abs(final))
    if peak > 0:
        final = final / peak * 0.85
    gap3 = np.zeros(int(SAMPLE_RATE * 0.04))
    sounds[SoundType.ONE_EIGHTY] = np.concatenate([e1, gap3, e2, gap3, e3, gap3, final])

    # Save all
    for sound_type, data in sounds.items():
        filepath = str(SOUNDS_DIR / f"{sound_type.value}.wav")
        _save_wav(filepath, data)
        logger.info(f"Generated sound: {filepath}")


class SoundManager(QObject):
    """
    Manages sound effect playback.
    Auto-generates WAV files on first run, then uses QSoundEffect for playback.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._effects: dict[SoundType, QSoundEffect] = {}
        self._enabled = True
        self._volume = 0.7

        # Generate sounds if they don't exist
        if not (SOUNDS_DIR / "dart_hit.wav").exists():
            logger.info("Generating sound effects...")
            _generate_all_sounds()

        # Load all sound effects
        for st in SoundType:
            filepath = SOUNDS_DIR / f"{st.value}.wav"
            if filepath.exists():
                effect = QSoundEffect(self)
                effect.setSource(QUrl.fromLocalFile(str(filepath)))
                effect.setVolume(self._volume)
                self._effects[st] = effect

    def play(self, sound_type: SoundType):
        """Play a sound effect."""
        if not self._enabled:
            return

        effect = self._effects.get(sound_type)
        if effect:
            effect.play()

    def play_for_score(self, value: int, multiplier: int, is_bull: bool,
                       is_miss: bool, turn_total: int = 0):
        """Play the appropriate sound for a dart score."""
        if is_miss:
            self.play(SoundType.DART_MISS)
        elif is_bull:
            self.play(SoundType.DART_BULL)
        elif multiplier == 3:
            self.play(SoundType.DART_TRIPLE)
        elif multiplier == 2:
            self.play(SoundType.DART_DOUBLE)
        else:
            self.play(SoundType.DART_HIT)

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = max(0.0, min(1.0, value))
        for effect in self._effects.values():
            effect.setVolume(self._volume)
