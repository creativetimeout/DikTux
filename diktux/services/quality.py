"""Transcription quality filter, ported from TranscriptionQualityService."""

from __future__ import annotations

MINIMUM_RECORDING_DURATION = 0.3


def should_reject_recording(duration: float) -> bool:
    return duration < MINIMUM_RECORDING_DURATION


def cleaned_transcript(text: str) -> str:
    return text.strip()


def is_likely_artifact(text: str, recording_duration: float) -> bool:
    cleaned = cleaned_transcript(text)
    if not cleaned:
        return True

    words = cleaned.split()
    letters = sum(1 for ch in cleaned if ch.isalpha())

    if letters == 0:
        return True

    if recording_duration < 0.55 and (len(words) >= 5 or len(cleaned) >= 32):
        return True

    if recording_duration < 0.8 and len(cleaned) >= 56:
        return True

    return False
