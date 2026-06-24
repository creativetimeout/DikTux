# DikTux

Voice dictation daemon for Linux — speak, transcribe, paste. Inspired by [Blitztext](https://github.com/jvossen/blitztext-app) for macOS.

## What it does

DikTux runs in the background with a system tray icon. Press a global hotkey to start recording, release to stop. Your speech is transcribed via Whisper and automatically pasted into the active application.

### Workflows

| Workflow | Description | Default Hotkey |
|---|---|---|
| **Diktat** | Basic speech-to-text | Super+Shift |
| **Lokales Diktat** | Offline transcription (no network) | Super+Shift+Ctrl |
| **Text-Verbesserung** | Transcribe + improve/rewrite | Super+Ctrl |
| **Dampf Ablassen** | Turn frustrated speech into calm, professional text | Super+Alt |
| **Emoji-Text** | Transcribe + add fitting emojis | Super+Ctrl+Alt |

All hotkeys are fully configurable via the settings UI.

## Features

- Remote transcription via OpenAI Whisper API
- Local transcription via faster-whisper (offline, private)
- LLM-powered text improvement, tone adjustment, and emoji insertion
- Works on both X11 and Wayland
- System tray icon with animated status feedback
- GTK4 settings UI
- Secure credential storage via GNOME Keyring / KDE Wallet
- Hold mode (hold key to record) and toggle mode (press to start/stop)

## Requirements

- Linux (Ubuntu 24.04+, other distros should work)
- Python 3.11+
- OpenAI API key (for remote transcription and LLM features)

## Installation

### System dependencies (Ubuntu/Debian)

```bash
sudo apt install libgirepository-2.0-dev gir1.2-gtk-4.0 \
    gir1.2-ayatanaappindicator3-0.1 libportaudio2 \
    wl-clipboard wtype xdotool xclip
```

Grant hotkey access (requires re-login):

```bash
sudo usermod -aG input $USER
```

### From source (current)

```bash
sudo apt install pipx
pipx ensurepath

git clone https://github.com/jvossen/diktux.git
cd diktux
pipx install ".[local]"
```

Without local Whisper (smaller install, no GPU dependencies):

```bash
pipx install "."
```

For development:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[local,gui,dev]"
```

### From PyPI (once published)

```bash
pipx install "diktux[local]"
```

## Usage

```bash
diktux
```

On first launch, the onboarding flow guides you through API key setup and microphone testing. After that, DikTux runs in the system tray — use the hotkeys to dictate.

## Configuration

Settings are stored at `~/.config/diktux/settings.json` and can be edited via the tray icon's settings window.

## License

MIT
