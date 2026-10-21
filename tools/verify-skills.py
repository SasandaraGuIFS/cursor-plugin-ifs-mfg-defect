#!/usr/bin/env python3
"""Validate every skills/<dir>/SKILL.md against Cursor Agent-Plugin rules:
- YAML frontmatter present
- `name` matches directory and is [a-z0-9-], 1-64 chars
- `description` is 1-1024 chars
"""
from __future__ import annotations

import pathlib
import re
import sys

try:
    import yaml  # pyyaml
except ImportError:  # pragma: no cover
    print("Install pyyaml: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

NAME_RE = re.compile(r"^(?!.*--)[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
FM_RE = re.compile(r"(?s)^---\n(.*?)\n---")


def validate(root: pathlib.Path) -> int:
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        print(f"no skills/ under {root}", file=sys.stderr)
        return 1

    errors: list[str] = []
    checked = 0
    for d in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
        skill_md = d / "SKILL.md"
        if not skill_md.is_file():
            errors.append(f"{d.name}: SKILL.md missing")
            continue
        text = skill_md.read_text(encoding="utf-8")
        m = FM_RE.match(text)
        if not m:
            errors.append(f"{d.name}: no YAML frontmatter")
            continue
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError as e:
            errors.append(f"{d.name}: invalid YAML ({e})")
            continue

        name = fm.get("name", "")
        desc = fm.get("description", "")
        if not isinstance(name, str) or not NAME_RE.match(name) or len(name) > 64:
            errors.append(f"{d.name}: invalid name '{name}'")
        elif name != d.name:
            errors.append(f"{d.name}: frontmatter name '{name}' != dir name")
        if not isinstance(desc, str) or not (1 <= len(desc) <= 1024):
            errors.append(f"{d.name}: description len={len(desc) if isinstance(desc, str) else 'N/A'} out of 1-1024")
        else:
            print(f"OK  {d.name:35s} len={len(desc)}")
        checked += 1

    if errors:
        print("", file=sys.stderr)
        print("FAIL:", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1
    print(f"\nAll {checked} skills pass Cursor Agent-Plugin frontmatter rules.")
    return 0


if __name__ == "__main__":
    root = pathlib.Path(__file__).resolve().parent.parent
    sys.exit(validate(root))
