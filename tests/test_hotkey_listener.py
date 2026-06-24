from diktux.config import HotkeyConfig
from diktux.services.hotkey import (
    HotkeyEvent,
    HotkeyEventType,
    HotkeyListener,
    HotkeyMatcher,
)


def _listener_with_events():
    matcher = HotkeyMatcher(HotkeyConfig())
    events: list[HotkeyEvent] = []
    matcher.on_event = events.append
    listener = HotkeyListener(matcher)
    return listener, events


def test_feed_event_builds_pressed_set_and_fires_down():
    listener, events = _listener_with_events()
    listener.feed_event("KEY_LEFTMETA", 1)
    listener.feed_event("KEY_LEFTSHIFT", 1)
    assert listener.pressed_keys == {"KEY_LEFTMETA", "KEY_LEFTSHIFT"}
    assert events[-1] == HotkeyEvent(HotkeyEventType.DOWN, "transcription")


def test_feed_event_release_fires_up():
    listener, events = _listener_with_events()
    listener.feed_event("KEY_LEFTMETA", 1)
    listener.feed_event("KEY_LEFTSHIFT", 1)
    listener.feed_event("KEY_LEFTSHIFT", 0)
    assert events[-1] == HotkeyEvent(HotkeyEventType.UP, "transcription")


def test_feed_event_repeat_value_ignored_for_set():
    listener, _ = _listener_with_events()
    listener.feed_event("KEY_LEFTMETA", 1)
    listener.feed_event("KEY_LEFTMETA", 2)  # autorepeat
    assert listener.pressed_keys == {"KEY_LEFTMETA"}


def test_feed_event_escape_fires_cancel():
    listener, events = _listener_with_events()
    listener.feed_event("KEY_ESC", 1)
    assert events[-1] == HotkeyEvent(HotkeyEventType.CANCEL, None)
