from diktux.services.quality import (
    MINIMUM_RECORDING_DURATION,
    cleaned_transcript,
    is_likely_artifact,
    should_reject_recording,
)


def test_minimum_duration_constant():
    assert MINIMUM_RECORDING_DURATION == 0.3


def test_should_reject_short_recording():
    assert should_reject_recording(0.2) is True
    assert should_reject_recording(0.3) is False
    assert should_reject_recording(1.0) is False


def test_cleaned_transcript_strips():
    assert cleaned_transcript("  hallo \n") == "hallo"


def test_empty_text_is_artifact():
    assert is_likely_artifact("   ", recording_duration=2.0) is True


def test_no_letters_is_artifact():
    assert is_likely_artifact("12345 !!!", recording_duration=2.0) is True


def test_many_words_in_very_short_recording_is_artifact():
    assert is_likely_artifact(
        "eins zwei drei vier fuenf", recording_duration=0.5
    ) is True


def test_long_text_in_short_recording_is_artifact():
    text = "a" * 60
    assert is_likely_artifact(text, recording_duration=0.7) is True


def test_normal_transcript_is_not_artifact():
    assert is_likely_artifact("Hallo Welt", recording_duration=2.0) is False
