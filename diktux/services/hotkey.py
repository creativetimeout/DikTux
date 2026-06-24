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
