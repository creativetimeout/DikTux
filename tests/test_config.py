from pathlib import Path

from diktux.config import (
    Config,
    DampfAblassenSettings,
    EmojiDensity,
    HotkeyMode,
    TextTone,
    load_config,
    save_config,
)


def test_default_config_values():
    cfg = Config()
    assert cfg.app.hotkey_mode is HotkeyMode.HOLD
    assert cfg.transcription.language == "de"
    assert cfg.text_improvement.tone is TextTone.NEUTRAL
    assert cfg.emoji_text.emoji_density is EmojiDensity.MITTEL
    assert cfg.hotkeys.transcription.keys == ["KEY_LEFTMETA", "KEY_LEFTSHIFT"]
    assert cfg.hotkeys.local_transcription.keys == [
        "KEY_LEFTMETA",
        "KEY_LEFTSHIFT",
        "KEY_LEFTCTRL",
    ]


def test_dampf_ablassen_default_prompt_ported():
    settings = DampfAblassenSettings()
    assert settings.system_prompt.startswith(
        "Du erhältst ein emotional gesprochenes Transkript."
    )
    assert "Gib NUR die fertige Nachricht zurück." in settings.system_prompt


def test_save_and_load_roundtrip(tmp_path: Path):
    path = tmp_path / "settings.json"
    cfg = Config()
    cfg.transcription.language = "it"
    cfg.app.secure_local_mode_enabled = True
    cfg.text_improvement.custom_terms = ["DikTux", "PipeWire"]
    save_config(cfg, path)

    loaded = load_config(path)
    assert loaded.transcription.language == "it"
    assert loaded.app.secure_local_mode_enabled is True
    assert loaded.text_improvement.custom_terms == ["DikTux", "PipeWire"]
    assert loaded.app.hotkey_mode is HotkeyMode.HOLD


def test_load_missing_file_returns_defaults(tmp_path: Path):
    loaded = load_config(tmp_path / "does-not-exist.json")
    assert loaded.transcription.language == "de"
