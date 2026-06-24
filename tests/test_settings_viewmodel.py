from pathlib import Path

from diktux.config import Config, EmojiDensity, HotkeyMode, TextTone, load_config
from diktux.services.credentials import CredentialsStore, InMemoryBackend
from diktux.ui.settings_viewmodel import SettingsViewModel


def _vm(tmp_path: Path):
    path = tmp_path / "settings.json"
    config = Config()
    credentials = CredentialsStore(backend=InMemoryBackend())
    vm = SettingsViewModel(
        config=config,
        credentials=credentials,
        save=lambda cfg: __import__("diktux.config", fromlist=["save_config"]).save_config(cfg, path),
    )
    return vm, path


def test_set_language_persists(tmp_path: Path):
    vm, path = _vm(tmp_path)
    vm.set_language("it")
    assert load_config(path).transcription.language == "it"


def test_set_hotkey_mode(tmp_path: Path):
    vm, path = _vm(tmp_path)
    vm.set_hotkey_mode(HotkeyMode.TOGGLE)
    assert load_config(path).app.hotkey_mode is HotkeyMode.TOGGLE


def test_custom_terms_roundtrip(tmp_path: Path):
    vm, path = _vm(tmp_path)
    vm.set_custom_terms_text(" DikTux , PipeWire ,, ")
    assert load_config(path).text_improvement.custom_terms == ["DikTux", "PipeWire"]
    assert vm.custom_terms_text() == "DikTux, PipeWire"


def test_set_tone_and_density(tmp_path: Path):
    vm, path = _vm(tmp_path)
    vm.set_tone(TextTone.FORMAL)
    vm.set_emoji_density(EmojiDensity.VIEL)
    cfg = load_config(path)
    assert cfg.text_improvement.tone is TextTone.FORMAL
    assert cfg.emoji_text.emoji_density is EmojiDensity.VIEL


def test_set_hotkey(tmp_path: Path):
    vm, path = _vm(tmp_path)
    vm.set_hotkey("transcription", ["KEY_LEFTMETA", "KEY_LEFTALT"])
    assert load_config(path).hotkeys.transcription.keys == [
        "KEY_LEFTMETA",
        "KEY_LEFTALT",
    ]


def test_api_key_save_and_mask(tmp_path: Path):
    vm, _ = _vm(tmp_path)
    vm.save_api_key("sk-abcdefghij")
    assert vm.masked_api_key().startswith("sk-a")
    vm.save_api_key("")
    assert vm.masked_api_key() == ""
