"""Settings dataclasses and JSON persistence (XDG-compliant)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path


class HotkeyMode(str, Enum):
    HOLD = "hold"
    TOGGLE = "toggle"


class TextTone(str, Enum):
    FORMAL = "formal"
    NEUTRAL = "neutral"
    CASUAL = "casual"


class EmojiDensity(str, Enum):
    WENIG = "wenig"
    MITTEL = "mittel"
    VIEL = "viel"


DAMPF_ABLASSEN_DEFAULT_PROMPT = (
    "Du erhältst ein emotional gesprochenes Transkript. Erkenne zuerst das "
    "eigentliche Ziel, Anliegen und den wahren Frust der Person. Formuliere "
    "daraus eine klare, respektvolle und wirksame Nachricht, mit der die Person "
    "ihr Ziel eher erreicht. Bewahre relevante Fakten, konkrete Probleme, "
    "Grenzen, Erwartungen und die nötige Dringlichkeit. Entferne Beleidigungen, "
    "Drohungen, Sarkasmus, Unterstellungen und unnötige Eskalation. Wenn mehrere "
    "Vorwürfe genannt werden, verdichte sie auf die entscheidenden Kernpunkte. "
    "Der Ton soll ruhig, menschlich, bestimmt und lösungsorientiert sein. Gib "
    "NUR die fertige Nachricht zurück."
)


@dataclass
class HotkeyBinding:
    keys: list[str] = field(default_factory=list)


@dataclass
class HotkeyConfig:
    mode: HotkeyMode = HotkeyMode.HOLD
    transcription: HotkeyBinding = field(
        default_factory=lambda: HotkeyBinding(["KEY_LEFTMETA", "KEY_LEFTSHIFT"])
    )
    local_transcription: HotkeyBinding = field(
        default_factory=lambda: HotkeyBinding(
            ["KEY_LEFTMETA", "KEY_LEFTSHIFT", "KEY_LEFTCTRL"]
        )
    )
    text_improver: HotkeyBinding = field(
        default_factory=lambda: HotkeyBinding(["KEY_LEFTMETA", "KEY_LEFTCTRL"])
    )
    dampf_ablassen: HotkeyBinding = field(
        default_factory=lambda: HotkeyBinding(["KEY_LEFTMETA", "KEY_LEFTALT"])
    )
    emoji_text: HotkeyBinding = field(
        default_factory=lambda: HotkeyBinding(
            ["KEY_LEFTMETA", "KEY_LEFTCTRL", "KEY_LEFTALT"]
        )
    )


@dataclass
class TranscriptionSettings:
    language: str = "de"


@dataclass
class TextImprovementSettings:
    system_prompt: str = ""
    custom_terms: list[str] = field(default_factory=list)
    context: str = ""
    tone: TextTone = TextTone.NEUTRAL
    custom_name: str = ""


@dataclass
class DampfAblassenSettings:
    system_prompt: str = DAMPF_ABLASSEN_DEFAULT_PROMPT
    custom_name: str = ""


@dataclass
class EmojiTextSettings:
    emoji_density: EmojiDensity = EmojiDensity.MITTEL
    custom_name: str = ""


@dataclass
class AppSettings:
    hotkey_mode: HotkeyMode = HotkeyMode.HOLD
    has_seen_onboarding: bool = False
    secure_local_mode_enabled: bool = False
    selected_local_model_name: str = "small"


@dataclass
class Config:
    app: AppSettings = field(default_factory=AppSettings)
    transcription: TranscriptionSettings = field(default_factory=TranscriptionSettings)
    text_improvement: TextImprovementSettings = field(
        default_factory=TextImprovementSettings
    )
    dampf_ablassen: DampfAblassenSettings = field(
        default_factory=DampfAblassenSettings
    )
    emoji_text: EmojiTextSettings = field(default_factory=EmojiTextSettings)
    hotkeys: HotkeyConfig = field(default_factory=HotkeyConfig)


DEFAULT_HOTKEYS = HotkeyConfig()


def settings_path() -> Path:
    base = Path.home() / ".config" / "diktux"
    return base / "settings.json"


def _binding_from_dict(data: dict) -> HotkeyBinding:
    return HotkeyBinding(keys=list(data.get("keys", [])))


def _hotkeys_from_dict(data: dict) -> HotkeyConfig:
    defaults = HotkeyConfig()
    return HotkeyConfig(
        mode=HotkeyMode(data.get("mode", HotkeyMode.HOLD.value)),
        transcription=_binding_from_dict(data.get("transcription", {}))
        if "transcription" in data
        else defaults.transcription,
        local_transcription=_binding_from_dict(data.get("local_transcription", {}))
        if "local_transcription" in data
        else defaults.local_transcription,
        text_improver=_binding_from_dict(data.get("text_improver", {}))
        if "text_improver" in data
        else defaults.text_improver,
        dampf_ablassen=_binding_from_dict(data.get("dampf_ablassen", {}))
        if "dampf_ablassen" in data
        else defaults.dampf_ablassen,
        emoji_text=_binding_from_dict(data.get("emoji_text", {}))
        if "emoji_text" in data
        else defaults.emoji_text,
    )


def _config_from_dict(data: dict) -> Config:
    app_data = data.get("app", {})
    app = AppSettings(
        hotkey_mode=HotkeyMode(app_data.get("hotkey_mode", HotkeyMode.HOLD.value)),
        has_seen_onboarding=bool(app_data.get("has_seen_onboarding", False)),
        secure_local_mode_enabled=bool(
            app_data.get("secure_local_mode_enabled", False)
        ),
        selected_local_model_name=app_data.get("selected_local_model_name", "small"),
    )
    tr_data = data.get("transcription", {})
    transcription = TranscriptionSettings(language=tr_data.get("language", "de"))

    ti_data = data.get("text_improvement", {})
    text_improvement = TextImprovementSettings(
        system_prompt=ti_data.get("system_prompt", ""),
        custom_terms=list(ti_data.get("custom_terms", [])),
        context=ti_data.get("context", ""),
        tone=TextTone(ti_data.get("tone", TextTone.NEUTRAL.value)),
        custom_name=ti_data.get("custom_name", ""),
    )

    da_data = data.get("dampf_ablassen", {})
    dampf_ablassen = DampfAblassenSettings(
        system_prompt=da_data.get("system_prompt", DAMPF_ABLASSEN_DEFAULT_PROMPT),
        custom_name=da_data.get("custom_name", ""),
    )

    em_data = data.get("emoji_text", {})
    emoji_text = EmojiTextSettings(
        emoji_density=EmojiDensity(
            em_data.get("emoji_density", EmojiDensity.MITTEL.value)
        ),
        custom_name=em_data.get("custom_name", ""),
    )

    hotkeys = _hotkeys_from_dict(data.get("hotkeys", {}))

    return Config(
        app=app,
        transcription=transcription,
        text_improvement=text_improvement,
        dampf_ablassen=dampf_ablassen,
        emoji_text=emoji_text,
        hotkeys=hotkeys,
    )


def load_config(path: Path | None = None) -> Config:
    target = path or settings_path()
    if not target.exists():
        return Config()
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return Config()
    return _config_from_dict(data)


def save_config(config: Config, path: Path | None = None) -> None:
    target = path or settings_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(asdict(config), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
