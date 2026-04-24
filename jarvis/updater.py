from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import requests

from jarvis.utils.config import settings


def check_for_update(current_version: str) -> tuple[bool, str]:
    if not settings.update_manifest_url:
        return False, "Update manifest URL is not configured."

    resp = requests.get(settings.update_manifest_url, timeout=10)
    if resp.status_code != 200:
        return False, "Failed to fetch update metadata."
    payload = resp.json()
    latest_version = payload.get("version")
    installer_url = payload.get("installer_url")
    if not latest_version or not installer_url:
        return False, "Invalid update manifest format."
    if latest_version == current_version:
        return False, "You are already on the latest version."

    tmp_dir = Path(tempfile.gettempdir())
    installer_path = tmp_dir / f"jarvis-{latest_version}.exe"
    data = requests.get(installer_url, timeout=20)
    data.raise_for_status()
    installer_path.write_bytes(data.content)
    subprocess.Popen([str(installer_path)])
    return True, f"Launching installer for version {latest_version}."
