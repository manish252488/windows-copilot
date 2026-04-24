"""Set Settings.version in jarvis/utils/config.py from a tag like v1.2.3 (CI / local)."""
from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: ci_set_version_from_tag.py <tag>", file=sys.stderr)
        return 1
    tag = sys.argv[1].strip()
    ver = tag[1:] if tag.startswith("v") else tag
    p = Path("jarvis/utils/config.py")
    t = p.read_text(encoding="utf-8")
    t2, n = re.subn(
        r'version: str = "[^"]*"',
        f'version: str = "{ver}"',
        t,
        count=1,
    )
    if n != 1:
        print("ERROR: could not find version: str in config.py", file=sys.stderr)
        return 1
    p.write_text(t2, encoding="utf-8")
    print(f"Updated {p} -> version: str = {ver!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
