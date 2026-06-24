"""System tray controller backed by pystray."""

from __future__ import annotations

from collections.abc import Callable

from diktux.state import TrayStatus
from diktux.ui.tray_icons import make_icon

DISPLAY_NAMES = {
    "transcription": "Diktat",
    "local_transcription": "Lokales Diktat",
    "text_improver": "Text-Verbesserung",
    "dampf_ablassen": "Dampf Ablassen",
    "emoji_text": "Emoji-Text",
}


def tooltip_for(status: TrayStatus, workflow_name: str | None = None) -> str:
    name = DISPLAY_NAMES.get(workflow_name or "", None)
    if status is TrayStatus.IDLE:
        return "DikTux ist bereit"
    if status is TrayStatus.RECORDING:
        return f"{name}: Aufnahme läuft" if name else "DikTux: Aufnahme läuft"
    if status is TrayStatus.PROCESSING:
        return f"{name}: Verarbeitung läuft" if name else "DikTux: Verarbeitung läuft"
    if status is TrayStatus.SUCCESS:
        return f"{name}: Fertig" if name else "DikTux: Fertig"
    return f"{name}: Fehler" if name else "DikTux: Fehler"


class TrayController:
    def __init__(
        self,
        on_open_settings: Callable[[], None] | None = None,
        on_quit: Callable[[], None] | None = None,
        icon_factory: Callable[[TrayStatus, int], object] | None = None,
    ) -> None:
        self._on_open_settings = on_open_settings or (lambda: None)
        self._on_quit = on_quit or (lambda: None)
        self._icon_factory = icon_factory or (
            lambda status, frame: make_icon(status, frame)
        )
        self.current_status = TrayStatus.IDLE
        self.current_tooltip = tooltip_for(TrayStatus.IDLE)
        self._icon = None

    def build_menu(self) -> list[tuple[str, Callable[[], None]]]:
        return [
            ("Einstellungen…", self._on_open_settings),
            ("Beenden", self._on_quit),
        ]

    def set_status(
        self, status: TrayStatus, workflow_name: str | None = None
    ) -> None:
        self.current_status = status
        self.current_tooltip = tooltip_for(status, workflow_name)
        image = self._icon_factory(status, 0)
        if self._icon is not None:
            self._icon.icon = image
            self._icon.title = self.current_tooltip

    def run(self) -> None:
        import pystray

        menu = pystray.Menu(
            *[
                pystray.MenuItem(label, (lambda cb: lambda icon, item: cb())(callback))
                for label, callback in self.build_menu()
            ]
        )
        self._icon = pystray.Icon(
            "diktux",
            icon=self._icon_factory(self.current_status, 0),
            title=self.current_tooltip,
            menu=menu,
        )
        self._icon.run()

    def stop(self) -> None:
        if self._icon is not None:
            self._icon.stop()
