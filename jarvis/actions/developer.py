from __future__ import annotations

import subprocess
from pathlib import Path


def _git_root_for(path: Path) -> Path | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(path),
            capture_output=True,
            text=True,
            timeout=8,
            shell=False,
        )
        if result.returncode != 0:
            return None
        out = (result.stdout or "").strip()
        return Path(out) if out else None
    except Exception:
        return None


def _resolve_git_cwd(cwd: str | None = None) -> str | None:
    candidates: list[Path] = []
    if cwd:
        candidates.append(Path(cwd))
    candidates.append(Path.cwd())
    # Project root (windows-jarvis) from this file location.
    candidates.append(Path(__file__).resolve().parents[2])
    # Home as last local fallback.
    candidates.append(Path.home())

    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate.resolve()) if candidate.exists() else str(candidate)
        if key in seen:
            continue
        seen.add(key)
        root = _git_root_for(candidate)
        if root is not None:
            return str(root)
    return None


def resolve_git_repo_path(cwd: str | None = None) -> str | None:
    return _resolve_git_cwd(cwd)


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
    git_cwd = _resolve_git_cwd(cwd)
    if not git_cwd:
        return "I could not find a git repository. Tell me the project folder path first."
    return run_terminal_command("git status", cwd=git_cwd)


def git_pull(cwd: str | None = None) -> str:
    git_cwd = _resolve_git_cwd(cwd)
    if not git_cwd:
        return "I could not find a git repository. Tell me the project folder path first."
    return run_terminal_command("git pull", cwd=git_cwd)


def git_push(cwd: str | None = None) -> str:
    git_cwd = _resolve_git_cwd(cwd)
    if not git_cwd:
        return "I could not find a git repository. Tell me the project folder path first."
    return run_terminal_command("git push", cwd=git_cwd)


def git_commit(message: str = "Update from Jarvis", cwd: str | None = None) -> str:
    git_cwd = _resolve_git_cwd(cwd)
    if not git_cwd:
        return "I could not find a git repository. Tell me the project folder path first."
    clean_msg = (message or "").strip() or "Update from Jarvis"
    clean_msg = clean_msg.replace('"', "'")
    return run_terminal_command(f'git add . && git commit -m "{clean_msg}"', cwd=git_cwd)


def git_commit_and_push(message: str = "Update from Jarvis", cwd: str | None = None) -> str:
    commit_out = git_commit(message=message, cwd=cwd)
    if "nothing to commit" in commit_out.lower():
        return commit_out
    if "error" in commit_out.lower() or "fatal" in commit_out.lower():
        return commit_out
    push_out = git_push(cwd=cwd)
    return f"{commit_out}\n\n{push_out}"[:1200]
