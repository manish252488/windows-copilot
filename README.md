# Jarvis for Windows (Python + OpenAI)

A modular voice assistant with Tkinter UI, speech input, LLM reasoning, system/web/developer actions, memory, logging, and Windows packaging support (install/uninstall/update flow).

## Features

- Microphone listening with ambient-noise calibration.
- Speech-to-text using OpenAI Whisper API (fallback Google SpeechRecognition).
- Jarvis personality with OpenAI GPT model and short-term memory.
- Text-to-speech with interrupt support.
- Command router for:
  - Windows controls (open/close apps, volume, lock, shutdown, restart, file search)
  - Web actions (open website, Google search, YouTube search, weather, news)
  - Developer actions (terminal commands, git status/pull/push)
- Optional wake-word mode (`jarvis` by default).
- Floating Tkinter desktop UI.
- Persistent memory + rotating logs.
- Buildable `.exe`, installer, uninstall entry (via Inno Setup), and update checker.

## Project Structure

```text
main.py
jarvis/
  speech/
    listener.py
    tts.py
  brain/
    llm.py
    memory.py
  actions/
    system.py
    web.py
    developer.py
    router.py
  utils/
    config.py
    logger.py
  updater.py
scripts/
  build_exe.ps1
  build_installer.ps1
installer/
  jarvis_installer.iss
```

## Setup

1. Install Python 3.10+.
2. Create and activate venv:
   - `python -m venv .venv`
   - `.venv\Scripts\activate`
3. Install dependencies:
   - `pip install -r requirements.txt`
4. Configure env:
   - `copy .env.example .env`
   - Set `OPENAI_API_KEY`.
   - For Indian accent English, keep `STT_LOCALE=en-IN` (default).
   - Optional speech tuning:
     - `STT_LOCALE=en-IN` (Indian English), `hi-IN` (Hindi), `en-US` (US English)
     - `WHISPER_LANGUAGE=en` or `hi`
   - Optional: `WEATHER_API_KEY`, `NEWS_API_KEY`, `UPDATE_MANIFEST_URL`.
5. Run:
   - `python main.py`

## Example Voice Commands

- `Jarvis, open chrome`
- `Jarvis, google latest python releases`
- `Jarvis, youtube node js tutorials`
- `Jarvis, weather in Mumbai`
- `Jarvis, run npm start`
- `Jarvis, git status`
- `Jarvis, lock screen`
- `Jarvis, volume down`
- `Jarvis, open chrome and youtube lo-fi focus`

## Wake Word

- `WAKE_WORD_ENABLED=1` (default): only commands with wake word are executed.
- `WAKE_WORD_ENABLED=0`: always-active listening.

## Installer / Uninstaller / Updates

### Build executable

```powershell
./scripts/build_exe.ps1 -Version 0.1.0
```

### Build installer (Inno Setup required)

```powershell
./scripts/build_installer.ps1 -Version 0.1.0
```

- Generated installer includes standard Windows uninstall entry automatically.

### Updates

Set `UPDATE_MANIFEST_URL` to a JSON endpoint:

```json
{
  "version": "0.2.0",
  "installer_url": "https://example.com/Jarvis-Setup-0.2.0.exe"
}
```

Use **Check Updates** button in the app.

## Notes for Production

- Add allow-lists/confirmation prompts for risky commands like shutdown.
- Replace hard-coded app mappings with user-configurable aliases.
- Add unit tests for routing and actions.
- Consider local Whisper model for full offline mode.
