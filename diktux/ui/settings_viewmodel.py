"""Pure-logic view model behind the GTK4 settings window (testable)."""

from __future__ import annotations

from diktux.config import (
    Config,
    EmojiDensity,
    HotkeyBinding,
    HotkeyMode,
    TextTone,
    save_config,
)
from diktux.services.credentials import CredentialsStore
from diktux.services.local_transcription import LocalTranscriptionService


class SettingsViewModel:
    def __init__(
        self,
        config: Config,
        credentials: CredentialsStore,
        save=save_config,
        local_transcription_service: LocalTranscriptionService | None = None,
    ) -> None:
        self.config = config
        self._credentials = credentials
        self._save = save
        self.local_transcription_service = local_transcription_service or LocalTranscriptionService()

    def persist(self) -> None:
        self._save(self.config)

    def set_language(self, value: str) -> None:
        self.config.transcription.language = value.strip()
        self.persist()

    def set_hotkey_mode(self, mode: HotkeyMode) -> None:
        self.config.app.hotkey_mode = mode
        self.config.hotkeys.mode = mode
        self.persist()

    def set_tone(self, tone: TextTone) -> None:
        self.config.text_improvement.tone = tone
        self.persist()

    def set_emoji_density(self, density: EmojiDensity) -> None:
        self.config.emoji_text.emoji_density = density
        self.persist()

    def set_custom_terms_text(self, text: str) -> None:
        terms = [part.strip() for part in text.split(",")]
        self.config.text_improvement.custom_terms = [t for t in terms if t]
        self.persist()

    def custom_terms_text(self) -> str:
        return ", ".join(self.config.text_improvement.custom_terms)

    def set_secure_local_mode(self, enabled: bool) -> None:
        self.config.app.secure_local_mode_enabled = enabled
        self.persist()

    def set_local_model(self, model_name: str) -> None:
        self.config.app.selected_local_model_name = model_name
        self.persist()

    def set_hotkey(self, workflow_name: str, keys: list[str]) -> None:
        setattr(self.config.hotkeys, workflow_name, HotkeyBinding(keys=list(keys)))
        self.persist()

    def save_api_key(self, value: str) -> None:
        value = value.strip()
        if value:
            self._credentials.set_api_key(value)
        else:
            self._credentials.delete_api_key()

    def masked_api_key(self) -> str:
        return self._credentials.masked_api_key()
