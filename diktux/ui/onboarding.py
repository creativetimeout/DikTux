"""First-run onboarding logic: API key, permissions, CLI tool checks."""

from __future__ import annotations

import shutil

from diktux.config import Config, save_config
from diktux.services.credentials import CredentialsStore


def input_group_ok(groups: list[str]) -> bool:
    return "input" in groups


def required_cli_tools(session_type: str) -> list[str]:
    if session_type == "wayland":
        return ["wl-copy", "wtype"]
    return ["xclip", "xdotool"]


def missing_cli_tools(session_type: str, which=shutil.which) -> list[str]:
    return [tool for tool in required_cli_tools(session_type) if which(tool) is None]


class OnboardingViewModel:
    def __init__(
        self,
        config: Config,
        credentials: CredentialsStore,
        save=save_config,
    ) -> None:
        self.config = config
        self._credentials = credentials
        self._save = save

    def is_configured(self) -> bool:
        return self._credentials.is_configured()

    def should_show(self) -> bool:
        return not self.is_configured() and not self.config.app.has_seen_onboarding

    def save_api_key(self, value: str) -> None:
        value = value.strip()
        if value:
            self._credentials.set_api_key(value)

    def complete(self) -> None:
        self.config.app.has_seen_onboarding = True
        self._save(self.config)
