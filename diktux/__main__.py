"""Entry point: wires real components and starts the daemon."""

from __future__ import annotations

import asyncio
import os
import signal
import sys
import threading


def _ensure_utf8_io() -> None:
    import os
    os.environ.setdefault("PYTHONIOENCODING", "utf-8:replace")
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name)
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def main() -> None:
    _ensure_utf8_io()
    from diktux import __version__
    from diktux.app import Application
    from diktux.config import load_config
    from diktux.services.audio_recorder import AudioRecorder
    from diktux.services.credentials import CredentialsStore
    from diktux.services.hotkey import HotkeyListener, HotkeyMatcher
    from diktux.services.llm import LLMService
    from diktux.services.paste import PasteService
    from diktux.services.local_transcription import LocalTranscriptionService
    from diktux.services.transcription import RemoteTranscriptionService
    from diktux.state import StateManager
    from diktux.ui.tray import TrayController

    config = load_config()
    credentials = CredentialsStore()
    paste_service = PasteService()
    transcriber = RemoteTranscriptionService(credentials=credentials)
    local_transcriber = LocalTranscriptionService(
        default_model=config.app.selected_local_model_name,
    )
    llm = LLMService(credentials=credentials)

    loop = asyncio.new_event_loop()

    def loop_runner(coro):
        asyncio.run_coroutine_threadsafe(coro, loop)

    def reload_config(_signum=None, _frame=None):
        new_config = load_config()
        app.config = new_config
        matcher._hotkeys = new_config.hotkeys
        local_transcriber._default_model = new_config.app.selected_local_model_name
        print("[DikTux] Einstellungen neu geladen.", file=sys.stderr)

    signal.signal(signal.SIGUSR1, reload_config)

    def open_settings():
        from diktux.ui.settings_window import open_settings_window

        open_settings_window(daemon_pid=os.getpid())

    tray = TrayController(
        on_open_settings=open_settings,
        on_quit=lambda: (listener.stop(), tray.stop(), loop.call_soon_threadsafe(loop.stop)),
    )

    state = StateManager(
        paste_service=paste_service,
        on_tray_status=lambda status: tray.set_status(status),
        on_error_message=lambda msg: print(f"[DikTux] Fehler: {msg}", file=sys.stderr),
    )
    app = Application(
        config=config,
        credentials=credentials,
        paste_service=paste_service,
        recorder_factory=lambda: AudioRecorder(),
        transcriber=transcriber,
        local_transcriber=local_transcriber,
        state=state,
        llm=llm,
        loop_runner=loop_runner,
    )

    matcher = HotkeyMatcher(config.hotkeys)
    matcher.on_event = app.handle_hotkey_event
    listener = HotkeyListener(matcher)

    loop_thread = threading.Thread(target=loop.run_forever, daemon=True)
    loop_thread.start()
    listener.start()

    print(f"DikTux {__version__} gestartet. Hotkeys aktiv, Tray-Icon wird angezeigt.")
    if not credentials.is_configured():
        print("Hinweis: Kein OpenAI API Key konfiguriert. Remote-Funktionen deaktiviert.", file=sys.stderr)

    try:
        tray.run()
    except KeyboardInterrupt:
        pass
    finally:
        listener.stop()
        loop.call_soon_threadsafe(loop.stop)
        loop_thread.join(timeout=2)


if __name__ == "__main__":
    main()
