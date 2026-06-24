"""Records microphone audio into a 16 kHz mono WAV file via sounddevice."""

from __future__ import annotations

import math
import uuid
import wave
from pathlib import Path
from tempfile import gettempdir

import numpy as np


class AudioRecorder:
    SAMPLE_RATE = 16000
    CHANNELS = 1

    def __init__(self, stream_factory=None, tmp_dir: Path | None = None) -> None:
        self._stream_factory = stream_factory or self._default_stream_factory
        self._tmp_dir = Path(tmp_dir) if tmp_dir else Path(gettempdir())
        self._stream = None
        self._chunks: list[np.ndarray] = []
        self._current_path: Path | None = None
        self.is_recording = False
        self.audio_level = 0.0
        self.last_duration = 0.0

    def _default_stream_factory(self, callback):
        import sounddevice as sd

        return sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=self.CHANNELS,
            dtype="float32",
            callback=lambda indata, frames, time_info, status: callback(
                indata.copy(), frames, time_info, status
            ),
        )

    def _make_path(self) -> Path:
        return self._tmp_dir / f"diktux-{uuid.uuid4().hex}.wav"

    def _normalize_level(self, rms: float) -> float:
        if rms <= 0:
            return 0.0
        power_db = 20.0 * math.log10(rms)
        normalized = (power_db + 50.0) / 50.0
        return max(0.0, min(1.0, normalized))

    def _on_frames(self, indata, frames, time_info, status) -> None:
        block = np.asarray(indata, dtype=np.float32)
        self._chunks.append(block)
        rms = float(np.sqrt(np.mean(np.square(block)))) if block.size else 0.0
        self.audio_level = self._normalize_level(rms)

    def start(self) -> None:
        self._chunks = []
        self.audio_level = 0.0
        self.last_duration = 0.0
        self._current_path = self._make_path()
        self._stream = self._stream_factory(self._on_frames)
        self.is_recording = True
        self._stream.start()

    def stop(self) -> Path:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        self.is_recording = False
        self.audio_level = 0.0

        if self._chunks:
            data = np.concatenate(self._chunks, axis=0)
        else:
            data = np.zeros((0, self.CHANNELS), dtype=np.float32)

        self.last_duration = len(data) / float(self.SAMPLE_RATE)

        clipped = np.clip(data, -1.0, 1.0)
        pcm16 = (clipped * 32767.0).astype("<i2")

        path = self._current_path or self._make_path()
        with wave.open(str(path), "wb") as wav:
            wav.setnchannels(self.CHANNELS)
            wav.setsampwidth(2)
            wav.setframerate(self.SAMPLE_RATE)
            wav.writeframes(pcm16.tobytes())

        self._current_path = path
        return path

    def discard(self) -> None:
        if self._current_path and self._current_path.exists():
            self._current_path.unlink()
        self._current_path = None
        self._chunks = []
