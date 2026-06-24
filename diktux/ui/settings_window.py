"""GTK4 settings window. Runs in a subprocess to avoid GTK3/GTK4 conflict with pystray."""

from __future__ import annotations

import subprocess
import sys

from diktux.config import EmojiDensity, HotkeyMode, TextTone
from diktux.ui.settings_viewmodel import SettingsViewModel

GTK_AVAILABLE = True


_HOTKEY_MODES = [HotkeyMode.HOLD, HotkeyMode.TOGGLE]
_TONES = [TextTone.FORMAL, TextTone.NEUTRAL, TextTone.CASUAL]
_DENSITIES = [EmojiDensity.WENIG, EmojiDensity.MITTEL, EmojiDensity.VIEL]
_MODE_LABELS = {HotkeyMode.HOLD: "Halten", HotkeyMode.TOGGLE: "Drücken"}
_TONE_LABELS = {
    TextTone.FORMAL: "Formell",
    TextTone.NEUTRAL: "Neutral",
    TextTone.CASUAL: "Locker",
}
_DENSITY_LABELS = {
    EmojiDensity.WENIG: "Wenig",
    EmojiDensity.MITTEL: "Mittel",
    EmojiDensity.VIEL: "Viel",
}


def open_settings_window(view_model: SettingsViewModel) -> None:
    subprocess.Popen(
        [sys.executable, "-m", "diktux.ui.settings_window"],
        start_new_session=True,
    )


def _build_window(Gtk, view_model: SettingsViewModel):
    app = Gtk.Application(application_id="de.diktux.settings")

    def on_activate(app):
        window = Gtk.ApplicationWindow(application=app, title="DikTux Einstellungen")
        window.set_default_size(480, 560)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)
        window.set_child(box)

        box.append(Gtk.Label(label="OpenAI API Key", xalign=0))
        api_entry = Gtk.Entry()
        api_entry.set_visibility(False)
        api_entry.set_placeholder_text(view_model.masked_api_key() or "sk-...")
        api_entry.connect(
            "changed", lambda e: view_model.save_api_key(e.get_text())
        )
        box.append(api_entry)

        box.append(Gtk.Label(label="Sprache (z. B. de, it, en)", xalign=0))
        lang_entry = Gtk.Entry()
        lang_entry.set_text(view_model.config.transcription.language)
        lang_entry.connect("changed", lambda e: view_model.set_language(e.get_text()))
        box.append(lang_entry)

        box.append(Gtk.Label(label="Hotkey-Modus", xalign=0))
        mode_dropdown = Gtk.DropDown.new_from_strings(
            [_MODE_LABELS[m] for m in _HOTKEY_MODES]
        )
        mode_dropdown.set_selected(_HOTKEY_MODES.index(view_model.config.app.hotkey_mode))
        mode_dropdown.connect(
            "notify::selected",
            lambda d, _p: view_model.set_hotkey_mode(_HOTKEY_MODES[d.get_selected()]),
        )
        box.append(mode_dropdown)

        box.append(Gtk.Label(label="Ton der Textverbesserung", xalign=0))
        tone_dropdown = Gtk.DropDown.new_from_strings([_TONE_LABELS[t] for t in _TONES])
        tone_dropdown.set_selected(_TONES.index(view_model.config.text_improvement.tone))
        tone_dropdown.connect(
            "notify::selected",
            lambda d, _p: view_model.set_tone(_TONES[d.get_selected()]),
        )
        box.append(tone_dropdown)

        box.append(Gtk.Label(label="Emoji-Dichte", xalign=0))
        density_dropdown = Gtk.DropDown.new_from_strings(
            [_DENSITY_LABELS[d] for d in _DENSITIES]
        )
        density_dropdown.set_selected(
            _DENSITIES.index(view_model.config.emoji_text.emoji_density)
        )
        density_dropdown.connect(
            "notify::selected",
            lambda d, _p: view_model.set_emoji_density(_DENSITIES[d.get_selected()]),
        )
        box.append(density_dropdown)

        box.append(Gtk.Label(label="Eigennamen / Fachbegriffe (kommasepariert)", xalign=0))
        terms_entry = Gtk.Entry()
        terms_entry.set_text(view_model.custom_terms_text())
        terms_entry.connect(
            "changed", lambda e: view_model.set_custom_terms_text(e.get_text())
        )
        box.append(terms_entry)

        secure_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        secure_row.append(Gtk.Label(label="Sicherer lokaler Modus", xalign=0, hexpand=True))
        secure_switch = Gtk.Switch()
        secure_switch.set_active(view_model.config.app.secure_local_mode_enabled)
        secure_switch.connect(
            "notify::active",
            lambda s, _p: view_model.set_secure_local_mode(s.get_active()),
        )
        secure_row.append(secure_switch)
        box.append(secure_row)

        window.present()

    app.connect("activate", on_activate)
    return app


def _main():
    import gi

    gi.require_version("Gtk", "4.0")
    from gi.repository import Gtk

    from diktux.config import load_config
    from diktux.services.credentials import CredentialsStore

    config = load_config()
    credentials = CredentialsStore()
    vm = SettingsViewModel(config=config, credentials=credentials)
    app = _build_window(Gtk, vm)
    app.run()


if __name__ == "__main__":
    _main()
