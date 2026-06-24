from diktux.state import TrayStatus
from diktux.ui.tray import DISPLAY_NAMES, TrayController, tooltip_for


def test_tooltip_idle():
    assert tooltip_for(TrayStatus.IDLE) == "DikTux ist bereit"


def test_tooltip_recording_with_name():
    assert (
        tooltip_for(TrayStatus.RECORDING, "transcription")
        == "Diktat: Aufnahme läuft"
    )


def test_tooltip_processing_with_name():
    assert (
        tooltip_for(TrayStatus.PROCESSING, "text_improver")
        == "Text-Verbesserung: Verarbeitung läuft"
    )


def test_tooltip_error_without_name():
    assert tooltip_for(TrayStatus.ERROR) == "DikTux: Fehler"


def test_display_names_cover_all_workflows():
    assert DISPLAY_NAMES["dampf_ablassen"] == "Dampf Ablassen"
    assert DISPLAY_NAMES["emoji_text"] == "Emoji-Text"
    assert DISPLAY_NAMES["local_transcription"] == "Lokales Diktat"


def test_set_status_updates_state():
    icons = []

    def icon_factory(status, frame):
        icons.append((status, frame))
        return object()

    controller = TrayController(icon_factory=icon_factory)
    controller.set_status(TrayStatus.RECORDING, "transcription")
    assert controller.current_status is TrayStatus.RECORDING
    assert controller.current_tooltip == "Diktat: Aufnahme läuft"


def test_build_menu_has_settings_and_quit():
    opened = []
    quit_called = []
    controller = TrayController(
        on_open_settings=lambda: opened.append(True),
        on_quit=lambda: quit_called.append(True),
        icon_factory=lambda status, frame: object(),
    )
    menu = controller.build_menu()
    labels = [label for label, _ in menu]
    assert "Einstellungen…" in labels
    assert "Beenden" in labels
    dict(menu)["Beenden"]()
    assert quit_called == [True]
