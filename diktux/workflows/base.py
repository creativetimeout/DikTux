"""Abstract workflow base: record -> process -> output, with quality gating."""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from pathlib import Path

from diktux.services.quality import (
    cleaned_transcript,
    is_likely_artifact,
    should_reject_recording,
)


class WorkflowPhase(str, Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


class RecordingTooShortError(Exception):
    def __init__(self) -> None:
        super().__init__("Aufnahme war zu kurz.")


class ArtifactError(Exception):
    def __init__(self) -> None:
        super().__init__("Keine verwertbare Sprache erkannt.")


class BaseWorkflow:
    def __init__(self, recorder) -> None:
        self._recorder = recorder
        self.type = "base"
        self.phase = WorkflowPhase.IDLE
        self.is_recording = False
        self.on_output: Callable[[str], None] | None = None
        self.on_phase_change: Callable[[WorkflowPhase], None] | None = None
        self.on_error: Callable[[Exception], None] | None = None
        self._last_duration = 0.0

    def _set_phase(self, phase: WorkflowPhase) -> None:
        self.phase = phase
        if self.on_phase_change is not None:
            self.on_phase_change(phase)

    def start(self) -> None:
        self._recorder.start()
        self.is_recording = True
        self._set_phase(WorkflowPhase.RECORDING)

    def cancel(self) -> None:
        self._recorder.discard()
        self.is_recording = False
        self._set_phase(WorkflowPhase.IDLE)

    def reset(self) -> None:
        self.is_recording = False
        self._set_phase(WorkflowPhase.IDLE)

    async def process(self, audio_path: Path) -> str:
        raise NotImplementedError

    async def stop(self) -> None:
        audio_path = self._recorder.stop()
        self.is_recording = False
        duration = self._recorder.last_duration
        self._last_duration = duration

        if should_reject_recording(duration):
            self._fail(RecordingTooShortError())
            self._cleanup(audio_path)
            return

        self._set_phase(WorkflowPhase.PROCESSING)
        try:
            raw = await self.process(audio_path)
        except Exception as exc:
            self._fail(exc)
            return

        text = cleaned_transcript(raw)
        if is_likely_artifact(text, duration):
            self._fail(ArtifactError())
            return

        if self.on_output is not None:
            self.on_output(text)
        self._set_phase(WorkflowPhase.DONE)

    def _fail(self, error: Exception) -> None:
        if self.on_error is not None:
            self.on_error(error)
        self._set_phase(WorkflowPhase.ERROR)

    @staticmethod
    def _cleanup(audio_path: Path) -> None:
        try:
            audio_path.unlink()
        except OSError:
            pass
