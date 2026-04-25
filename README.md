# Jarvis for Windows (Python + OpenAI)

A modular voice assistant with a multi-screen Tkinter UI, speech input, LLM reasoning, system/web/developer actions, memory, logging, and Windows packaging support (install/uninstall/update flow).

## Features

- Microphone listening with ambient-noise calibration.
- Speech-to-text using OpenAI Whisper API (fallback Google SpeechRecognition).
- Jarvis personality with OpenAI GPT model and short-term memory.
- Text-to-speech with interrupt support.
- Command router for:
  - Windows controls (open/close apps, volume, lock, shutdown, restart, file search)
  - Web actions (open website, Google search, YouTube search, weather, news)
  - Developer actions (terminal commands, git status/pull/push)
- Microphone toggle mode with `F8` hotkey pause/resume.
- Multi-screen desktop UI:
  - Home (state + pulse visualization + latest snippet)
  - Conversation (full history + search + copy response)
  - Settings (theme/audio/AI/update controls)
  - Command Center (quick action cards)
- Refined visuals using `ttkbootstrap` (modern themed Tk UI) with existing custom animations.
- Persistent memory + rotating logs.
- Buildable `.exe`, installer, uninstall entry (via Inno Setup), and update checker.

## Project Structure

```text
main.py
jarvis/
  ui/
    app.py
    screens.py
    theme.py
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
   - Set your OpenAI API key from **Settings > AI Settings** inside the app.
   - For Indian accent English, keep `STT_LOCALE=en-IN` (default).
   - Optional speech tuning:
     - `STT_LOCALE=en-IN` (Indian English), `hi-IN` (Hindi), `en-US` (US English)
     - `WHISPER_LANGUAGE=en` or `hi`
     - `STT_PAUSE_THRESHOLD_SECONDS=2.0` (auto-submit after ~2s pause)
     - `STT_TIMEOUT_SECONDS=6`
     - `STT_PHRASE_TIME_LIMIT_SECONDS=20`
     - `STT_OPENAI_PROMPT=Indian English accent. Keep words exact. Preserve product names and commands.`
   - Optional weather defaults:
     - `WEATHER_DEFAULT_CITY=Mumbai`
     - `WEATHER_COUNTRY_CODE=IN`
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

## Microphone Toggle

- Use the mic toggle to turn listening on/off explicitly.
- Press `F8` to pause/resume listening.

## Weather troubleshooting

- Make sure `WEATHER_API_KEY` is valid (OpenWeather API key).
- For generic commands like `weather` or `what's the weather today`, Jarvis uses:
  - `WEATHER_DEFAULT_CITY`
  - `WEATHER_COUNTRY_CODE`
- Example:
  - `WEATHER_DEFAULT_CITY=Mumbai`
  - `WEATHER_COUNTRY_CODE=IN`

## Installer / Uninstaller / Updates

### Build executable (stable name for reputation)

```powershell
./scripts/build_exe.ps1 -Version 1.0.0
```

- Produces `dist/Jarvis-Assistant/Jarvis-Assistant.exe`.

### Build installer (Inno Setup required)

```powershell
./scripts/build_installer.ps1 -Version 1.0.0
```

- Produces `installer/output/Jarvis-Assistant-Setup-1.0.0.exe`.
- Includes standard uninstall entry, Start Menu shortcut, optional desktop shortcut, and modern setup UI.
- Uses stable app and file names to improve SmartScreen reputation over time.

### Trust explanation for end users

Include `RELEASE-NOTES.txt` in your release description or package so users know how to proceed if SmartScreen appears:

- Click **More info**
- Click **Run anyway**
- Explain that warning appears because the app is not yet signed with a trusted certificate.

### Reputation and signing checklist

- Keep output names stable (`Jarvis-Assistant.exe`, `Jarvis-Assistant-Setup-x.y.z.exe`).
- Keep publisher string stable (`Manish Singh`).
- Prefer direct `.exe` / installer uploads in GitHub Releases (not only ZIP).
- Optional local self-signing:
  - `New-SelfSignedCertificate -Type CodeSigningCert -Subject "CN=Manish Singh"`
  - `signtool sign /fd SHA256 /a Jarvis-Assistant.exe`
- Consider MSIX as an advanced packaging option for cleaner install behavior.

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
