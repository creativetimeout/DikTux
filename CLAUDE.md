# DikTux

## Purpose

Linux port of the macOS app "Blitztext" (`../blitztext-app`). A background daemon with GTK4 UI that provides voice dictation via global hotkeys. Records audio, transcribes via Whisper (remote API or local faster-whisper), optionally processes text through an LLM, and auto-pastes results into the active application.

## Tech Stack

- **Language:** Python 3.11+ (use `tomllib`, modern type hints)
- **Audio:** `sounddevice` + `soundfile` → WAV 16kHz mono 16-bit PCM
- **Remote Transcription:** `httpx` → OpenAI Whisper API (`whisper-1`)
- **Local Transcription:** `faster-whisper` (CTranslate2, optional `[local]` extra)
- **LLM:** `httpx` → OpenAI Chat Completions (`gpt-4o-mini` for text improvement/emoji, `gpt-4o` for calm-down)
- **Global Hotkeys:** `evdev` (kernel-level, works on X11 and Wayland, requires `input` group)
- **System Tray:** `pystray` + `Pillow` (icon generation)
- **Settings UI:** GTK4 via `PyGObject`
- **Credentials:** `secretstorage` (GNOME Keyring / KDE Wallet)
- **Auto-Paste:** `xclip`/`xdotool` (X11) or `wl-copy`/`wtype` (Wayland), `ydotool` as fallback
- **Tests:** `pytest` + `pytest-asyncio`

## Implementation Plan

Full specification with 26 TDD tasks: `docs/superpowers/plans/2026-06-23-diktux.md`

Execute with: `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans`

## Conventions

- Code identifiers and comments: English
- User-facing strings (UI, error messages, tooltips): German, ported from macOS original
- XDG paths: config at `~/.config/diktux/`, models at `~/.local/share/diktux/`
- Conventional Commits (`feat:`, `test:`, `chore:`)
- TDD mandatory: failing test → minimal implementation → commit

## Architecture

```
diktux/
  __main__.py              # Entry point
  app.py                   # Application lifecycle
  state.py                 # Central StateManager
  config.py                # Settings dataclasses + JSON persistence

  services/
    audio_recorder.py      # sounddevice → WAV
    transcription.py       # OpenAI Whisper API
    local_transcription.py # faster-whisper
    llm.py                 # OpenAI Chat Completions + system prompts
    hotkey.py              # evdev hotkey monitoring
    paste.py               # Clipboard + Ctrl+V (X11/Wayland detection)
    credentials.py         # secretstorage
    quality.py             # Transcription quality filter

  workflows/
    base.py                # Workflow base class
    transcription.py       # Basic dictation
    text_improvement.py    # Dictation + text improvement
    calm_down.py           # Dictation + calm-down rewrite
    emoji_text.py          # Dictation + emoji insertion

  ui/
    tray.py                # System tray (pystray)
    tray_icons.py          # Icon generation (Pillow)
    settings_window.py     # GTK4 settings window
    onboarding.py          # First-run setup
```

## Workflows

Each workflow follows: record → transcribe → (optional LLM) → auto-paste

| Workflow | Default Hotkey | LLM Model |
|---|---|---|
| Diktat | Super+Shift | none |
| Lokales Diktat | Super+Shift+Ctrl | none (local whisper only) |
| Text-Verbesserung | Super+Ctrl | gpt-4o-mini |
| Dampf Ablassen | Super+Alt | gpt-4o |
| Emoji-Text | Super+Ctrl+Alt | gpt-4o-mini |

Hotkeys are fully configurable via settings UI.

## System Dependencies (Ubuntu 24.04)

```bash
sudo apt install libgirepository-2.0-dev gir1.2-gtk-4.0 \
    gir1.2-ayatanaappindicator3-0.1 libportaudio2 \
    wl-clipboard wtype xdotool xclip
sudo usermod -aG input $USER  # for evdev hotkey access
```

## macOS Reference

The original Swift/SwiftUI source is at `../blitztext-app`. Key files for porting reference:
- `BlitztextMac/Services/LLMService.swift` — system prompts (port verbatim)
- `BlitztextMac/Services/TranscriptionQualityService.swift` — quality filter logic
- `BlitztextMac/Features/Workflows/WorkflowProtocol.swift` — workflow data model
- `BlitztextMac/App/AppState.swift` — state management + auto-paste logic
