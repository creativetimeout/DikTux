import math
import wave
from pathlib import Path

import numpy as np

from diktux.services.audio_recorder import AudioRecorder


class FakeStream:
    """Stand-in for sounddevice.InputStream that feeds preset frames."""

    def __init__(self, callback, frames_list):
        self._callback = callback
        self._frames_list = frames_list
        self.started = False
        self.stopped = False

    def start(self):
        self.started = True
        for frames in self._frames_list:
            self._callback(frames, len(frames), None, None)

    def stop(self):
        self.stopped = True

    def close(self):
        pass


def test_normalize_level_silence_is_zero():
    rec = AudioRecorder()
    assert rec._normalize_level(0.0) == 0.0


def test_normalize_level_full_scale_is_one():
    rec = AudioRecorder()
    assert math.isclose(rec._normalize_level(1.0), 1.0, abs_tol=1e-6)


def test_normalize_level_midrange():
    rec = AudioRecorder()
    rms = 10 ** (-25 / 20)
    assert math.isclose(rec._normalize_level(rms), 0.5, abs_tol=1e-3)


def test_start_stop_writes_wav(tmp_path: Path):
    tone = (np.ones((1600, 1), dtype=np.float32) * 0.5)
    frames_list = [tone, tone]

    def stream_factory(callback):
        return FakeStream(callback, frames_list)

    rec = AudioRecorder(stream_factory=stream_factory, tmp_dir=tmp_path)
    rec.start()
    assert rec.is_recording is True
    path = rec.stop()
    assert rec.is_recording is False
    assert path.exists()
    assert path.suffix == ".wav"

    with wave.open(str(path), "rb") as wav:
        assert wav.getframerate() == 16000
        assert wav.getnchannels() == 1
        assert wav.getsampwidth() == 2
        assert wav.getnframes() == 3200
    assert math.isclose(rec.last_duration, 0.2, abs_tol=1e-3)


def test_discard_removes_file(tmp_path: Path):
    tone = np.ones((1600, 1), dtype=np.float32) * 0.5

    def stream_factory(callback):
        return FakeStream(callback, [tone])

    rec = AudioRecorder(stream_factory=stream_factory, tmp_dir=tmp_path)
    rec.start()
    path = rec.stop()
    assert path.exists()
    rec.discard()
    assert not path.exists()
