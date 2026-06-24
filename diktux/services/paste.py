"""Clipboard handling and Ctrl+V simulation for X11 and Wayland."""

from __future__ import annotations

import subprocess
from collections.abc import Mapping


def detect_session_type(env: Mapping[str, str] | None = None) -> str:
    import os

    source = env if env is not None else os.environ
    value = (source.get("XDG_SESSION_TYPE") or "").strip().lower()
    return "wayland" if value == "wayland" else "x11"


def _default_runner(cmd: list[str], input: bytes | None = None) -> int:
    completed = subprocess.run(cmd, input=input, check=False)
    return completed.returncode


class PasteService:
    def __init__(self, session_type: str | None = None, runner=None, env=None) -> None:
        self.session_type = session_type or detect_session_type(env)
        self._runner = runner or _default_runner

    def clipboard_command(self) -> list[str]:
        if self.session_type == "wayland":
            return ["wl-copy"]
        return ["xclip", "-selection", "clipboard"]

    def paste_command(self) -> list[str]:
        if self.session_type == "wayland":
            return ["wtype", "-M", "ctrl", "v", "-m", "ctrl"]
        return ["xdotool", "key", "ctrl+v"]

    def _fallback_paste_command(self) -> list[str]:
        return ["ydotool", "key", "29:1", "47:1", "47:0", "29:0"]

    def copy_to_clipboard(self, text: str) -> None:
        self._runner(self.clipboard_command(), input=text.encode("utf-8"))

    def paste(self, text: str) -> None:
        self.copy_to_clipboard(text)
        code = self._runner(self.paste_command(), input=None)
        if code != 0:
            self._runner(self._fallback_paste_command(), input=None)
