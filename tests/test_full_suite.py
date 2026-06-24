import importlib


def test_all_core_modules_importable():
    modules = [
        "diktux.config",
        "diktux.state",
        "diktux.app",
        "diktux.services.credentials",
        "diktux.services.audio_recorder",
        "diktux.services.transcription",
        "diktux.services.local_transcription",
        "diktux.services.llm",
        "diktux.services.hotkey",
        "diktux.services.paste",
        "diktux.services.quality",
        "diktux.workflows.base",
        "diktux.workflows.transcription",
        "diktux.workflows.text_improvement",
        "diktux.workflows.calm_down",
        "diktux.workflows.emoji_text",
        "diktux.ui.tray",
        "diktux.ui.tray_icons",
        "diktux.ui.settings_viewmodel",
        "diktux.ui.settings_window",
        "diktux.ui.onboarding",
    ]
    for name in modules:
        assert importlib.import_module(name) is not None


def test_entry_point_main_exists():
    from diktux.__main__ import main

    assert callable(main)
