"""Global hotkey detection via evdev and combo matching logic."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from diktux.config import HotkeyConfig

WORKFLOW_NAMES = (
    "transcription",
    "local_transcription",
    "text_improver",
    "dampf_ablassen",
    "emoji_text",
)


class HotkeyEventType(str, Enum):
    DOWN = "down"
    UP = "up"
    CANCEL = "cancel"


@dataclass(frozen=True)
class HotkeyEvent:
    type: HotkeyEventType
    workflow: str | None


class HotkeyMatcher:
    def __init__(self, hotkeys: HotkeyConfig) -> None:
        self._hotkeys = hotkeys
        self._active_combo: str | None = None
        self.on_event: Callable[[HotkeyEvent], None] | None = None

    def _bindings(self) -> list[tuple[str, frozenset[str]]]:
        pairs = []
        for name in WORKFLOW_NAMES:
            binding = getattr(self._hotkeys, name)
            if binding.keys:
                pairs.append((name, frozenset(binding.keys)))
        pairs.sort(key=lambda item: len(item[1]), reverse=True)
        return pairs

    def _match(self, pressed: frozenset[str]) -> str | None:
        for name, keys in self._bindings():
            if keys and keys.issubset(pressed) and keys == pressed:
                return name
        return None

    def _emit(self, event: HotkeyEvent) -> None:
        if self.on_event is not None:
            self.on_event(event)

    def update_keys(self, pressed: set[str]) -> None:
        matched = self._match(frozenset(pressed))

        if matched is not None:
            if self._active_combo is None:
                self._active_combo = matched
                self._emit(HotkeyEvent(HotkeyEventType.DOWN, matched))
            return

        if self._active_combo is not None:
            combo = self._active_combo
            self._active_combo = None
            self._emit(HotkeyEvent(HotkeyEventType.UP, combo))

    def escape_pressed(self) -> None:
        self._active_combo = None
        self._emit(HotkeyEvent(HotkeyEventType.CANCEL, None))


import threading


class HotkeyListener:
    def __init__(self, matcher: HotkeyMatcher, device_factory=None) -> None:
        self._matcher = matcher
        self._device_factory = device_factory or self._default_device_factory
        self.pressed_keys: set[str] = set()
        self._thread: threading.Thread | None = None
        self._running = False

    @staticmethod
    def _default_device_factory():
        import evdev

        devices = []
        for path in evdev.list_devices():
            device = evdev.InputDevice(path)
            caps = device.capabilities()
            if evdev.ecodes.EV_KEY in caps:
                devices.append(device)
        return devices

    def feed_event(self, key_name: str, value: int) -> None:
        if key_name == "KEY_ESC" and value == 1:
            self._matcher.escape_pressed()
            return

        if value == 1:
            self.pressed_keys.add(key_name)
        elif value == 0:
            self.pressed_keys.discard(key_name)

        self._matcher.update_keys(self.pressed_keys)

    def _run(self) -> None:
        import evdev
        import select

        devices = self._device_factory()
        fd_to_device = {dev.fd: dev for dev in devices}
        while self._running:
            ready, _, _ = select.select(fd_to_device, [], [], 0.5)
            for fd in ready:
                device = fd_to_device[fd]
                for event in device.read():
                    if event.type != evdev.ecodes.EV_KEY:
                        continue
                    key_name = evdev.ecodes.KEY.get(event.code)
                    if isinstance(key_name, list):
                        key_name = key_name[0]
                    if key_name:
                        self.feed_event(key_name, event.value)

    def start(self) -> None:
        if self._thread is not None:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None
