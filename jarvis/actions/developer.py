from __future__ import annotations

import subprocess
from pathlib import Path


def run_terminal_command(command: str, cwd: str | None = None) -> str:
    working_dir = cwd or str(Path.home())
    try:
        result = subprocess.run(
            command,
            cwd=working_dir,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = (result.stdout or result.stderr).strip()
        if not output:
            output = f"Command exited with code {result.returncode}."
        return output[:1200]
    except Exception as exc:
        return f"Command execution failed: {exc}"


def git_status(cwd: str | None = None) -> str:
    return run_terminal_command("git status", cwd=cwd)


def git_pull(cwd: str | None = None) -> str:
    return run_terminal_command("git pull", cwd=cwd)


def git_push(cwd: str | None = None) -> str:
    return run_terminal_command("git push", cwd=cwd)
