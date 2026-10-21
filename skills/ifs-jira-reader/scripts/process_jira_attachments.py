"""
Download Jira attachments and prepare them for defect analysis.

- Downloads all attachments for an issue
- Converts Word documents (.docx, .doc) to Markdown when direct read is not possible
- Extracts embedded media from Word docs and references them from the generated .md files
- Writes ATTACHMENTS.md index for the agent to read

Usage:
    python process_jira_attachments.py <issue_key> [--output-dir <dir>]

Environment variables (same as download_attachments.py):
    JIRA_USER_EMAIL, JIRA_API_TOKEN, JIRA_SITE_URL (optional)

Optional dependencies (install for best Word conversion):
    pip install mammoth

Fallback: .docx text is extracted via stdlib (zip + XML) if mammoth is not installed.
.doc files require pandoc on PATH, or remain as binary originals with a stub .md note.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any

WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}
TEXT_EXTENSIONS = {".txt", ".log", ".csv", ".json", ".xml", ".html", ".htm", ".md"}
OFFICE_WORD_EXTENSIONS = {".docx", ".doc"}


def get_credentials() -> tuple[str, str, str]:
    site_url = os.environ.get("JIRA_SITE_URL", "https://ifsdev.atlassian.net").rstrip("/")
    email = os.environ.get("JIRA_USER_EMAIL", "")
    token = os.environ.get("JIRA_API_TOKEN", "")
    if not email or not token:
        print("Error: JIRA_USER_EMAIL and JIRA_API_TOKEN environment variables required", file=sys.stderr)
        sys.exit(1)
    return site_url, email, token


def make_auth_header(email: str, token: str) -> str:
    credentials = base64.b64encode(f"{email}:{token}".encode()).decode()
    return f"Basic {credentials}"


def get_issue_attachments(site_url: str, issue_key: str, auth_header: str) -> list[dict[str, Any]]:
    url = f"{site_url}/rest/api/3/issue/{issue_key}?fields=attachment"
    req = urllib.request.Request(url)
    req.add_header("Authorization", auth_header)
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data.get("fields", {}).get("attachment", [])
    except urllib.error.HTTPError as e:
        print(f"Error fetching issue {issue_key}: {e.code} {e.reason}", file=sys.stderr)
        sys.exit(1)


def download_attachment(attachment: dict[str, Any], output_dir: Path, auth_header: str) -> Path | None:
    filename = attachment["filename"]
    content_url = attachment["content"]
    output_path = output_dir / filename

    counter = 1
    while output_path.exists():
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        output_path = output_dir / f"{stem}_{counter}{suffix}"
        counter += 1

    print(f"  Downloading: {filename}")

    req = urllib.request.Request(content_url)
    req.add_header("Authorization", auth_header)

    try:
        with urllib.request.urlopen(req) as response:
            output_path.write_bytes(response.read())
        print(f"  Saved: {output_path}")
        return output_path
    except urllib.error.HTTPError as e:
        print(f"  Failed to download {filename}: {e.code} {e.reason}", file=sys.stderr)
        return None


def slugify(name: str) -> str:
    stem = Path(name).stem
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", stem).strip("_") or "document"


def extract_docx_text_stdlib(docx_path: Path) -> str:
    paragraphs: list[str] = []
    with zipfile.ZipFile(docx_path) as zf:
        with zf.open("word/document.xml") as doc_xml:
            tree = ET.parse(doc_xml)
            for para in tree.findall(".//w:p", WORD_NS):
                parts: list[str] = []
                for node in para.findall(".//w:t", WORD_NS):
                    if node.text:
                        parts.append(node.text)
                line = "".join(parts).strip()
                if line:
                    paragraphs.append(line)
    return "\n\n".join(paragraphs)


def extract_docx_media(docx_path: Path, media_dir: Path, doc_slug: str) -> list[tuple[str, Path]]:
    extracted: list[tuple[str, Path]] = []
    media_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(docx_path) as zf:
        media_files = [name for name in zf.namelist() if name.startswith("word/media/")]
        for index, name in enumerate(media_files, start=1):
            suffix = Path(name).suffix.lower() or ".bin"
            target = media_dir / f"{doc_slug}_{index}{suffix}"
            with zf.open(name) as src, open(target, "wb") as dst:
                dst.write(src.read())
            extracted.append((name, target))
    return extracted


def convert_docx_with_mammoth(docx_path: Path, media_dir: Path, doc_slug: str) -> tuple[str, list[Path]] | None:
    try:
        import mammoth  # type: ignore
    except ImportError:
        return None

    media_dir.mkdir(parents=True, exist_ok=True)
    saved_media: list[Path] = []
    counter = {"n": 0}

    def convert_image(image: Any) -> dict[str, str]:
        counter["n"] += 1
        extension = "png"
        if image.content_type:
            extension = image.content_type.split("/")[-1].replace("jpeg", "jpg")
        target = media_dir / f"{doc_slug}_embedded_{counter['n']}.{extension}"
        with image.open() as image_bytes:
            target.write_bytes(image_bytes.read())
        saved_media.append(target)
        rel = target.as_posix()
        return {"src": rel}

    with docx_path.open("rb") as docx_file:
        result = mammoth.convert_to_markdown(docx_file, convert_image=mammoth.images.img_element(convert_image))

    return result.value, saved_media


def convert_docx_to_markdown(docx_path: Path, converted_dir: Path, media_root: Path) -> Path:
    doc_slug = slugify(docx_path.name)
    media_dir = media_root / doc_slug
    md_path = converted_dir / f"{doc_slug}.md"

    mammoth_result = convert_docx_with_mammoth(docx_path, media_dir, doc_slug)
    if mammoth_result:
        body, saved_media = mammoth_result
        header = [
            f"# {docx_path.name}",
            "",
            f"Source attachment: `{docx_path.name}`",
            f"Converted from Word (.docx) for defect analysis.",
            "",
        ]
        if saved_media:
            header.extend(["## Embedded media", ""])
            for media in saved_media:
                rel = media.relative_to(converted_dir.parent)
                if media.suffix.lower() in IMAGE_EXTENSIONS:
                    header.append(f"![{media.name}]({rel.as_posix()})")
                else:
                    header.append(f"- Media reference: `{rel.as_posix()}`")
            header.append("")
        header.extend(["## Document content", "", body])
        md_path.write_text("\n".join(header), encoding="utf-8")
        return md_path

    # Stdlib fallback: plain text + extracted word/media files
    text = extract_docx_text_stdlib(docx_path)
    embedded = extract_docx_media(docx_path, media_dir, doc_slug)
    lines = [
        f"# {docx_path.name}",
        "",
        f"Source attachment: `{docx_path.name}`",
        "Converted with stdlib fallback (install `mammoth` for richer Markdown).",
        "",
    ]
    if embedded:
        lines.extend(["## Embedded media", ""])
        for _, media_path in embedded:
            rel = media_path.relative_to(converted_dir.parent)
            if media_path.suffix.lower() in IMAGE_EXTENSIONS:
                lines.append(f"![{media_path.name}]({rel.as_posix()})")
            else:
                lines.append(f"- Media reference: `{rel.as_posix()}`")
        lines.append("")
    lines.extend(["## Document content", "", text or "*(No extractable text found)*"])
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path


def convert_doc_with_pandoc(doc_path: Path, converted_dir: Path) -> Path | None:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        return None

    doc_slug = slugify(doc_path.name)
    md_path = converted_dir / f"{doc_slug}.md"
    media_dir = converted_dir.parent / "media" / doc_slug
    media_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        pandoc,
        str(doc_path),
        "-t",
        "markdown",
        "-o",
        str(md_path),
        f"--extract-media={media_dir}",
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        print(f"  Pandoc failed for {doc_path.name}: {exc.stderr}", file=sys.stderr)
        return None

    prefix = [
        f"# {doc_path.name}",
        "",
        f"Source attachment: `{doc_path.name}`",
        "Converted from legacy Word (.doc) via pandoc.",
        "",
        "## Document content",
        "",
    ]
    existing = md_path.read_text(encoding="utf-8", errors="replace")
    md_path.write_text("\n".join(prefix) + existing, encoding="utf-8")
    return md_path


def write_stub_markdown(original: Path, converted_dir: Path, reason: str) -> Path:
    doc_slug = slugify(original.name)
    md_path = converted_dir / f"{doc_slug}.md"
    md_path.write_text(
        "\n".join(
            [
                f"# {original.name}",
                "",
                f"Source attachment: `{original.name}`",
                "",
                reason,
                "",
                f"Original file kept at: `{original.as_posix()}`",
            ]
        ),
        encoding="utf-8",
    )
    return md_path


def classify_attachment(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return "image"
    if suffix in VIDEO_EXTENSIONS:
        return "video"
    if suffix in OFFICE_WORD_EXTENSIONS:
        return "word"
    if suffix == ".pdf":
        return "pdf"
    if suffix in TEXT_EXTENSIONS:
        return "text"
    return "other"


def build_attachments_index(
    issue_key: str,
    output_dir: Path,
    entries: list[dict[str, str]],
) -> Path:
    index_path = output_dir / "ATTACHMENTS.md"
    lines = [
        f"# Jira attachments — {issue_key}",
        "",
        "Generated for defect analysis. Read converted Markdown files first; use original binaries when needed.",
        "",
        "| File | Type | Read path | Notes |",
        "|------|------|-----------|-------|",
    ]
    for entry in entries:
        lines.append(
            f"| {entry['filename']} | {entry['type']} | `{entry['read_path']}` | {entry['notes']} |"
        )

    converted = [e for e in entries if e.get("converted")]
    if converted:
        lines.extend(["", "## Converted documents", ""])
        for entry in converted:
            lines.append(f"- [{entry['filename']}]({entry['read_path']})")

    media_entries = [e for e in entries if e["type"] in {"image", "video"}]
    if media_entries:
        lines.extend(["", "## Media references", ""])
        for entry in media_entries:
            rel = entry["read_path"]
            if entry["type"] == "image":
                lines.append(f"![{entry['filename']}]({rel})")
            else:
                lines.append(f"- Video: `{rel}`")

    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return index_path


def process_downloaded_files(output_dir: Path, issue_key: str) -> Path:
    originals_dir = output_dir / "originals"
    converted_dir = output_dir / "converted"
    media_root = output_dir / "media"
    converted_dir.mkdir(parents=True, exist_ok=True)

    entries: list[dict[str, str]] = []

    for path in sorted(originals_dir.iterdir()):
        if not path.is_file():
            continue

        kind = classify_attachment(path)
        read_path = path.relative_to(output_dir).as_posix()
        notes = "Read directly"
        converted = False

        if kind == "word":
            if path.suffix.lower() == ".docx":
                md_path = convert_docx_to_markdown(path, converted_dir, media_root)
                read_path = md_path.relative_to(output_dir).as_posix()
                notes = "Converted .docx → Markdown"
                converted = True
            elif path.suffix.lower() == ".doc":
                md_path = convert_doc_with_pandoc(path, converted_dir)
                if md_path:
                    read_path = md_path.relative_to(output_dir).as_posix()
                    notes = "Converted .doc → Markdown (pandoc)"
                    converted = True
                else:
                    stub = write_stub_markdown(
                        path,
                        converted_dir,
                        "Legacy `.doc` file — install pandoc or open the original manually.",
                    )
                    read_path = stub.relative_to(output_dir).as_posix()
                    notes = "Stub only — pandoc not available"
                    converted = True
        elif kind == "image":
            notes = "Image — use Read tool or reference below"
        elif kind == "video":
            notes = "Video — reference path; transcribe or inspect manually if needed"
        elif kind == "pdf":
            notes = "PDF — read with Read tool (pages parameter if large)"
        elif kind == "text":
            notes = "Text — read directly"

        entries.append(
            {
                "filename": path.name,
                "type": kind,
                "read_path": read_path,
                "notes": notes,
                "converted": "true" if converted else "",
            }
        )

    return build_attachments_index(issue_key, output_dir, entries)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and prepare Jira attachments for defect analysis")
    parser.add_argument("issue_key", help="Jira issue key (e.g. MFZ-29917)")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (default: docs/<issue-key>/attachments)",
    )
    args = parser.parse_args()

    issue_key = args.issue_key.strip().upper()
    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else Path("docs") / issue_key / "attachments"
    )
    originals_dir = output_dir / "originals"
    originals_dir.mkdir(parents=True, exist_ok=True)

    site_url, email, token = get_credentials()
    auth_header = make_auth_header(email, token)

    print(f"Fetching attachments for {issue_key}...")
    attachments = get_issue_attachments(site_url, issue_key, auth_header)

    if not attachments:
        index = output_dir / "ATTACHMENTS.md"
        index.write_text(
            f"# Jira attachments — {issue_key}\n\nNo attachments on this issue.\n",
            encoding="utf-8",
        )
        print(f"No attachments found. Wrote {index}")
        return

    print(f"Found {len(attachments)} attachment(s)\n")
    for attachment in attachments:
        download_attachment(attachment, originals_dir, auth_header)

    index_path = process_downloaded_files(output_dir, issue_key)
    print(f"\nAttachment index: {index_path}")
    print("Read ATTACHMENTS.md and any converted/*.md files before continuing defect analysis.")


if __name__ == "__main__":
    main()
