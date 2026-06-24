"""GTK4 settings window. Runs in a subprocess to avoid GTK3/GTK4 conflict with pystray."""

from __future__ import annotations

import subprocess
import sys

import threading

from diktux.config import EmojiDensity, HotkeyMode, TextTone
from diktux.services.local_transcription import LocalTranscriptionService, SUPPORTED_MODELS
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
_MODEL_LIST = list(SUPPORTED_MODELS)
_MODEL_LABELS = {
    "small": "Small (schnell, ~500 MB)",
    "large-v3": "Large V3 (beste Qualität, ~3 GB)",
    "large-v3-turbo": "Large V3 Turbo (schnell + gut, ~1.5 GB)",
}


def open_settings_window(view_model=None, daemon_pid: int | None = None) -> None:
    cmd = [sys.executable, "-m", "diktux.ui.settings_window"]
    if daemon_pid is not None:
        cmd.extend(["--daemon-pid", str(daemon_pid)])
    subprocess.Popen(cmd, start_new_session=True)


def _build_window(Gtk, view_model: SettingsViewModel, daemon_pid: int | None = None):
    from gi.repository import Gio

    app = Gtk.Application(
        application_id="de.diktux.settings",
        flags=Gio.ApplicationFlags.NON_UNIQUE,
    )

    def on_activate(app):
        window = Gtk.ApplicationWindow(application=app, title="DikTux Einstellungen")
        window.set_default_size(480, 680)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        window.set_child(scrolled)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)
        scrolled.set_child(box)

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

        box.append(Gtk.Label(label="Lokales Whisper-Modell", xalign=0))
        model_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        model_dropdown = Gtk.DropDown.new_from_strings(
            [_MODEL_LABELS[m] for m in _MODEL_LIST]
        )
        model_dropdown.set_hexpand(True)
        current_model = view_model.config.app.selected_local_model_name
        if current_model in _MODEL_LIST:
            model_dropdown.set_selected(_MODEL_LIST.index(current_model))

        local_svc = view_model.local_transcription_service
        download_btn = Gtk.Button()
        download_spinner = Gtk.Spinner()

        def _update_download_btn(*_args):
            selected = _MODEL_LIST[model_dropdown.get_selected()]
            if local_svc.is_model_available(selected):
                download_btn.set_label("Vorhanden")
                download_btn.set_sensitive(False)
            else:
                download_btn.set_label("Herunterladen")
                download_btn.set_sensitive(True)

        def _on_download_clicked(_btn):
            selected = _MODEL_LIST[model_dropdown.get_selected()]
            download_btn.set_sensitive(False)
            download_btn.set_child(download_spinner)
            download_spinner.start()

            def _do_download():
                try:
                    local_svc._download_sync(selected)
                except Exception:
                    pass
                from gi.repository import GLib
                GLib.idle_add(_download_done)

            def _download_done():
                download_spinner.stop()
                download_btn.set_child(None)
                _update_download_btn()

            threading.Thread(target=_do_download, daemon=True).start()

        model_dropdown.connect(
            "notify::selected",
            lambda d, _p: (
                view_model.set_local_model(_MODEL_LIST[d.get_selected()]),
                _update_download_btn(),
            ),
        )
        download_btn.connect("clicked", _on_download_clicked)
        _update_download_btn()

        model_row.append(model_dropdown)
        model_row.append(download_btn)
        box.append(model_row)

        apply_btn = Gtk.Button(label="Übernehmen")
        apply_btn.add_css_class("suggested-action")
        status_label = Gtk.Label(label="", xalign=0.5)

        def _on_apply(_btn):
            if daemon_pid is not None:
                import os as _os
                import signal as _signal
                try:
                    _os.kill(daemon_pid, _signal.SIGUSR1)
                    status_label.set_text("Einstellungen übernommen.")
                except OSError:
                    status_label.set_text("DikTux-Daemon nicht erreichbar.")
            else:
                status_label.set_text("Kein laufender Daemon gefunden.")

        apply_btn.connect("clicked", _on_apply)
        box.append(apply_btn)
        box.append(status_label)

        window.present()

    app.connect("activate", on_activate)
    return app


def _main():
    import argparse

    import gi

    gi.require_version("Gtk", "4.0")
    from gi.repository import Gtk

    from diktux.config import load_config
    from diktux.services.credentials import CredentialsStore

    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon-pid", type=int, default=None)
    args = parser.parse_args()

    config = load_config()
    credentials = CredentialsStore()
    vm = SettingsViewModel(config=config, credentials=credentials)
    app = _build_window(Gtk, vm, daemon_pid=args.daemon_pid)
    app.run()


if __name__ == "__main__":
    _main()
