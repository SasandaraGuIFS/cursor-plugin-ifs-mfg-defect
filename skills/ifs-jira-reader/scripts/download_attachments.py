"""
Download Jira issue attachments to a local directory.

Usage:
    python download_attachments.py <issue_key> [--output-dir <dir>]

Environment variables:
    JIRA_USER_EMAIL - Jira account email
    JIRA_API_TOKEN  - Jira API token (generate at https://id.atlassian.com/manage-profile/security/api-tokens)
    JIRA_SITE_URL   - (Optional) Override site URL. Defaults to https://ifsdev.atlassian.net

Example:
    export JIRA_USER_EMAIL="user@example.com"
    export JIRA_API_TOKEN="your-api-token"
    python download_attachments.py HRZ-20567
    python download_attachments.py HRZ-20567 --output-dir /tmp/attachments
"""

import argparse
import base64
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path


def get_credentials():
    site_url = os.environ.get("JIRA_SITE_URL", "https://ifsdev.atlassian.net").rstrip("/")
    email = os.environ.get("JIRA_USER_EMAIL", "")
    token = os.environ.get("JIRA_API_TOKEN", "")
    if not email or not token:
        print("Error: JIRA_USER_EMAIL and JIRA_API_TOKEN environment variables required", file=sys.stderr)
        sys.exit(1)

    return site_url, email, token


def make_auth_header(email, token):
    credentials = base64.b64encode(f"{email}:{token}".encode()).decode()
    return f"Basic {credentials}"


def get_issue_attachments(site_url, issue_key, auth_header):
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
        if e.code == 404:
            print(f"Issue {issue_key} not found", file=sys.stderr)
        elif e.code == 401:
            print("Authentication failed — check JIRA_USER_EMAIL and JIRA_API_TOKEN", file=sys.stderr)
        sys.exit(1)


def download_attachment(attachment, output_dir, auth_header):
    filename = attachment["filename"]
    content_url = attachment["content"]
    size = attachment.get("size", 0)
    mime_type = attachment.get("mimeType", "unknown")

    output_path = output_dir / filename

    # Handle duplicate filenames
    counter = 1
    while output_path.exists():
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        output_path = output_dir / f"{stem}_{counter}{suffix}"
        counter += 1

    print(f"  Downloading: {filename} ({size} bytes, {mime_type})")

    req = urllib.request.Request(content_url)
    req.add_header("Authorization", auth_header)

    try:
        with urllib.request.urlopen(req) as response:
            with open(output_path, "wb") as f:
                f.write(response.read())
        print(f"  Saved: {output_path}")
        return str(output_path)
    except urllib.error.HTTPError as e:
        print(f"  Failed to download {filename}: {e.code} {e.reason}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(description="Download Jira issue attachments")
    parser.add_argument("issue_key", help="Jira issue key (e.g. HRZ-20567)")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (default: ./jira-attachments/<issue_key>)",
    )
    args = parser.parse_args()

    site_url, email, token = get_credentials()
    auth_header = make_auth_header(email, token)

    output_dir = Path(args.output_dir) if args.output_dir else Path("jira-attachments") / args.issue_key
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching attachments for {args.issue_key}...")
    attachments = get_issue_attachments(site_url, args.issue_key, auth_header)

    if not attachments:
        print(f"No attachments found on {args.issue_key}")
        return

    print(f"Found {len(attachments)} attachment(s):\n")

    downloaded = []
    for attachment in attachments:
        path = download_attachment(attachment, output_dir, auth_header)
        if path:
            downloaded.append(path)

    print(f"\nDownloaded {len(downloaded)}/{len(attachments)} attachment(s) to {output_dir}")

    # Print summary for Claude to parse
    print("\n--- Attachment Summary ---")
    for attachment in attachments:
        print(f"  {attachment['filename']} | {attachment.get('mimeType', 'unknown')} | {attachment.get('size', 0)} bytes")


if __name__ == "__main__":
    main()
