"""Entry point: wires real components and starts the daemon."""

from __future__ import annotations

import asyncio
import threading


def main() -> None:
    from diktux.app import Application
    from diktux.config import load_config
    from diktux.services.audio_recorder import AudioRecorder
    from diktux.services.credentials import CredentialsStore
    from diktux.services.hotkey import HotkeyListener, HotkeyMatcher
    from diktux.services.paste import PasteService
    from diktux.services.transcription import RemoteTranscriptionService
    from diktux.state import StateManager

    config = load_config()
    credentials = CredentialsStore()
    paste_service = PasteService()
    transcriber = RemoteTranscriptionService(credentials=credentials)

    loop = asyncio.new_event_loop()

    def loop_runner(coro):
        asyncio.run_coroutine_threadsafe(coro, loop)

    state = StateManager(paste_service=paste_service)
    app = Application(
        config=config,
        credentials=credentials,
        paste_service=paste_service,
        recorder_factory=lambda: AudioRecorder(),
        transcriber=transcriber,
        state=state,
        loop_runner=loop_runner,
    )

    matcher = HotkeyMatcher(config.hotkeys)
    matcher.on_event = app.handle_hotkey_event
    listener = HotkeyListener(matcher)

    loop_thread = threading.Thread(target=loop.run_forever, daemon=True)
    loop_thread.start()
    listener.start()

    try:
        loop_thread.join()
    except KeyboardInterrupt:
        listener.stop()


if __name__ == "__main__":
    main()
