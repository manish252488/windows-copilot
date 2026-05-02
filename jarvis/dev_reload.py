"""Development-only file watcher: restarts the process when Python sources change."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

_IGNORE_DIR_NAMES = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "dist",
        "build",
        ".pytest_cache",
        "node_modules",
        ".cursor",
    }
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _should_ignore_path(path: str) -> bool:
    try:
        parts = Path(path).resolve().parts
    except OSError:
        return True
    return any(p in _IGNORE_DIR_NAMES for p in parts)


class _RestartOnChange(FileSystemEventHandler):
    def __init__(self, debounce_sec: float = 0.35) -> None:
        self._debounce_sec = debounce_sec
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def on_modified(self, event: object) -> None:
        src_path = getattr(event, "src_path", "")
        if getattr(event, "is_directory", False):
            return
        if _should_ignore_path(src_path):
            return
        if not str(src_path).endswith(".py"):
            return
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self._debounce_sec, _spawn_restart)
            self._timer.daemon = True
            self._timer.start()

    # Created files (save-as, branch checkout) should also trigger.
    def on_created(self, event: object) -> None:
        self.on_modified(event)


def _spawn_restart() -> None:
    print("[jarvis dev] Source changed; restarting…", flush=True)
    args = [sys.executable, "-u", *sys.argv]
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
    try:
        subprocess.Popen(
            args,
            cwd=os.getcwd(),
            env=os.environ.copy(),
            close_fds=True,  # Avoid leaking FDs to child
            creationflags=creationflags,
        )
    except OSError as e:
        print(f"[jarvis dev] Failed to restart: {e}", flush=True)
        return
    os._exit(0)

def start_dev_reload() -> Observer:
    """Watch the repo for `.py` edits and restart this process (debounced)."""
    root = _repo_root()
    handler = _RestartOnChange()
    observer = Observer()
    observer.schedule(handler, str(root), recursive=True)
    observer.start()
    print(f"[jarvis dev] Watching {root} for changes (--reload).", flush=True)
    return observer
