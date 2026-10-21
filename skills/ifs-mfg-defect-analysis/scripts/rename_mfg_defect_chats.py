import sqlite3
import json
import os
import re
import argparse
from pathlib import Path

JIRA_KEY_RE = re.compile(r"\b(MFZ-\d+)\b", re.IGNORECASE)
MFG_SKILL_MARKERS = (
    "ifs-mfg-defect-analysis",
    "IFS Manufacturing Defect Analyzer",
)

CURSOR_GLOBAL_STATE = Path(os.environ.get("APPDATA", "")) / "Cursor" / "User" / "globalStorage" / "state.vscdb"
CURSOR_SEARCH_DB = Path(os.environ.get("APPDATA", "")) / "Cursor" / "User" / "globalStorage" / "conversation-search.db"
CURSOR_PROJECTS = Path.home() / ".cursor" / "projects"


def is_mfg_defect_transcript(text: str) -> bool:
    return any(marker in text for marker in MFG_SKILL_MARKERS)


def extract_jira_key(text: str) -> str | None:
    match = JIRA_KEY_RE.search(text)
    return match.group(1).upper() if match else None


def scan_transcripts(projects_root: Path) -> dict[str, str]:
    """Return composerId -> Jira key for mfg defect chats."""
    mapping: dict[str, str] = {}
    if not projects_root.exists():
        return mapping

    for jsonl in projects_root.glob("*/agent-transcripts/*/*.jsonl"):
        if "subagents" in jsonl.parts:
            continue
        composer_id = jsonl.parent.name
        try:
            content = jsonl.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if not is_mfg_defect_transcript(content):
            continue
        # Prefer early user messages; fall back to whole transcript.
        head = "\n".join(content.splitlines()[:20])
        key = extract_jira_key(head) or extract_jira_key(content)
        if key:
            mapping[composer_id] = key
    return mapping


def load_composer_headers(conn: sqlite3.Connection) -> dict[str, dict]:
    headers: dict[str, dict] = {}
    cur = conn.cursor()
    try:
        cur.execute("SELECT composerId, value FROM composerHeaders")
        for composer_id, value in cur.fetchall():
            try:
                headers[composer_id] = json.loads(value)
            except json.JSONDecodeError:
                headers[composer_id] = {}
    except sqlite3.OperationalError:
        pass

    cur.execute("SELECT key, value FROM ItemTable WHERE key = 'composer.composerHeaders'")
    row = cur.fetchone()
    if row:
        try:
            data = json.loads(row[1])
            for item in data.get("allComposers", []):
                cid = item.get("composerId")
                if cid:
                    headers.setdefault(cid, {}).update(item)
        except json.JSONDecodeError:
            pass
    return headers


def save_composer_header(conn: sqlite3.Connection, composer_id: str, header: dict) -> None:
    value = json.dumps(header, ensure_ascii=False)
    conn.execute(
        "INSERT INTO composerHeaders (composerId, value) VALUES (?, ?) "
        "ON CONFLICT(composerId) DO UPDATE SET value = excluded.value",
        (composer_id, value),
    )

    cur = conn.execute("SELECT value FROM ItemTable WHERE key = 'composer.composerHeaders'")
    row = cur.fetchone()
    if row:
        try:
            data = json.loads(row[0])
        except json.JSONDecodeError:
            data = {"allComposers": []}
        updated = False
        for item in data.get("allComposers", []):
            if item.get("composerId") == composer_id:
                item["name"] = header.get("name", item.get("name"))
                updated = True
                break
        if not updated:
            data.setdefault("allComposers", []).append(
                {"composerId": composer_id, "name": header.get("name")}
            )
        conn.execute(
            "UPDATE ItemTable SET value = ? WHERE key = 'composer.composerHeaders'",
            (json.dumps(data, ensure_ascii=False),),
        )


def update_search_title(conn: sqlite3.Connection, composer_id: str, title: str) -> bool:
    cur = conn.cursor()
    cur.execute("UPDATE conversations SET title = ? WHERE id = ?", (title, composer_id))
    return cur.rowcount > 0


def rename_chats(mapping: dict[str, str], dry_run: bool = True) -> list[tuple[str, str, str]]:
    """Return list of (composer_id, old_title, new_title)."""
    changes: list[tuple[str, str, str]] = []
    if not CURSOR_GLOBAL_STATE.exists():
        raise FileNotFoundError(f"Cursor state DB not found: {CURSOR_GLOBAL_STATE}")

    state_conn = sqlite3.connect(CURSOR_GLOBAL_STATE)
    search_conn = sqlite3.connect(CURSOR_SEARCH_DB) if CURSOR_SEARCH_DB.exists() else None
    headers = load_composer_headers(state_conn)

    search_titles: dict[str, str] = {}
    if search_conn:
        for cid, title in search_conn.execute("SELECT id, title FROM conversations"):
            search_titles[cid] = title or ""

    for composer_id, jira_key in sorted(mapping.items()):
        header = headers.get(composer_id, {})
        old_title = header.get("name") or search_titles.get(composer_id, "")
        if old_title == jira_key:
            continue
        changes.append((composer_id, old_title, jira_key))
        if dry_run:
            continue

        header["name"] = jira_key
        save_composer_header(state_conn, composer_id, header)
        if search_conn:
            update_search_title(search_conn, composer_id, jira_key)

    if not dry_run:
        state_conn.commit()
        if search_conn:
            search_conn.commit()

    state_conn.close()
    if search_conn:
        search_conn.close()
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rename past ifs-mfg-defect-analysis Cursor chats to their Jira key."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write changes to Cursor databases (default: dry run).",
    )
    parser.add_argument(
        "--projects-root",
        type=Path,
        default=CURSOR_PROJECTS,
        help="Path to ~/.cursor/projects",
    )
    args = parser.parse_args()

    mapping = scan_transcripts(args.projects_root)
    if not mapping:
        print("No mfg-defect-analysis transcripts with a Jira key found.")
        return 0

    changes = rename_chats(mapping, dry_run=not args.apply)
    mode = "APPLY" if args.apply else "DRY RUN"
    print(f"{mode}: {len(changes)} chat(s) to rename (of {len(mapping)} mfg defect chat(s) scanned)\n")
    for composer_id, old_title, new_title in changes:
        old_display = old_title or "(no title)"
        print(f"  {composer_id[:8]}...  {old_display!r}  ->  {new_title}")
    if not args.apply and changes:
        print("\nRe-run with --apply to write changes. Close Cursor first if titles do not refresh.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
