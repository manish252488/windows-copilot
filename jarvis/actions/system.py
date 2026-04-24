from __future__ import annotations

import os
import subprocess
from pathlib import Path

import psutil

try:
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
except Exception:  # pragma: no cover - optional dependency at runtime
    CLSCTX_ALL = None
    AudioUtilities = None
    IAudioEndpointVolume = None


APP_MAP = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "vscode": str(
        Path(os.getenv("LOCALAPPDATA", "")) / "Programs" / "Microsoft VS Code" / "Code.exe"
    ),
    "vs code": str(
        Path(os.getenv("LOCALAPPDATA", "")) / "Programs" / "Microsoft VS Code" / "Code.exe"
    ),
    "notepad": "notepad.exe",
}


def open_app(app_name: str) -> str:
    app_key = app_name.lower().strip()
    target = APP_MAP.get(app_key)
    if not target:
        return f"I do not know how to open '{app_name}' yet."
    try:
        subprocess.Popen(target)
        return f"Opening {app_name}."
    except Exception as exc:
        return f"Could not open {app_name}: {exc}"


def close_app(process_name: str) -> str:
    target = process_name.lower().replace(".exe", "")
    killed = 0
    for proc in psutil.process_iter(["name"]):
        name = (proc.info.get("name") or "").lower().replace(".exe", "")
        if target in name:
            proc.terminate()
            killed += 1
    return f"Closed {killed} matching process(es)." if killed else "No matching app found."


def lock_screen() -> str:
    os.system("rundll32.exe user32.dll,LockWorkStation")
    return "Locking your screen."


def shutdown() -> str:
    os.system("shutdown /s /t 5")
    return "System shutdown requested."


def restart() -> str:
    os.system("shutdown /r /t 5")
    return "System restart requested."


def _get_volume_controller() -> IAudioEndpointVolume:
    if not all([CLSCTX_ALL, AudioUtilities, IAudioEndpointVolume]):
        raise RuntimeError("Volume control dependencies are not installed.")
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return interface.QueryInterface(IAudioEndpointVolume)


def volume_up(step: float = 0.08) -> str:
    volume = _get_volume_controller()
    current = volume.GetMasterVolumeLevelScalar()
    volume.SetMasterVolumeLevelScalar(min(current + step, 1.0), None)
    return "Volume increased."


def volume_down(step: float = 0.08) -> str:
    volume = _get_volume_controller()
    current = volume.GetMasterVolumeLevelScalar()
    volume.SetMasterVolumeLevelScalar(max(current - step, 0.0), None)
    return "Volume decreased."


def mute() -> str:
    volume = _get_volume_controller()
    volume.SetMute(1, None)
    return "Muted."


def unmute() -> str:
    volume = _get_volume_controller()
    volume.SetMute(0, None)
    return "Unmuted."


def search_file(file_name: str, start_dir: str | None = None) -> str:
    root = Path(start_dir) if start_dir else Path.home()
    for path in root.rglob("*"):
        if file_name.lower() in path.name.lower():
            os.startfile(str(path))
            return f"Found and opened {path.name}."
    return f"No file matching '{file_name}' found."
