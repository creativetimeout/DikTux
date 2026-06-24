from diktux.config import HotkeyConfig
from diktux.services.hotkey import (
    HotkeyEvent,
    HotkeyEventType,
    HotkeyMatcher,
)


def _collect(matcher: HotkeyMatcher) -> list[HotkeyEvent]:
    events: list[HotkeyEvent] = []
    matcher.on_event = events.append
    return events


def test_down_then_up_transcription():
    matcher = HotkeyMatcher(HotkeyConfig())
    events = _collect(matcher)
    matcher.update_keys({"KEY_LEFTMETA", "KEY_LEFTSHIFT"})
    matcher.update_keys(set())
    assert events[0] == HotkeyEvent(HotkeyEventType.DOWN, "transcription")
    assert events[1] == HotkeyEvent(HotkeyEventType.UP, "transcription")


def test_down_fires_only_once_while_held():
    matcher = HotkeyMatcher(HotkeyConfig())
    events = _collect(matcher)
    matcher.update_keys({"KEY_LEFTMETA", "KEY_LEFTSHIFT"})
    matcher.update_keys({"KEY_LEFTMETA", "KEY_LEFTSHIFT"})
    down_events = [e for e in events if e.type is HotkeyEventType.DOWN]
    assert len(down_events) == 1


def test_more_specific_binding_wins():
    matcher = HotkeyMatcher(HotkeyConfig())
    events = _collect(matcher)
    matcher.update_keys({"KEY_LEFTMETA", "KEY_LEFTSHIFT", "KEY_LEFTCTRL"})
    assert events[0] == HotkeyEvent(HotkeyEventType.DOWN, "local_transcription")


def test_no_match_no_event():
    matcher = HotkeyMatcher(HotkeyConfig())
    events = _collect(matcher)
    matcher.update_keys({"KEY_A"})
    assert events == []


def test_escape_fires_cancel():
    matcher = HotkeyMatcher(HotkeyConfig())
    events = _collect(matcher)
    matcher.escape_pressed()
    assert events[0] == HotkeyEvent(HotkeyEventType.CANCEL, None)
