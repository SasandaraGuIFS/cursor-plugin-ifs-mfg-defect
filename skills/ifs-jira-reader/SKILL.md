---
name: ifs-jira-reader
description: This skill should be used when reading a Jira ticket for defect investigation, retrieving issue details from Jira, extracting the reported version and affected track, downloading Jira attachments, or reading Jira comments for context on a customer-reported issue. Triggers on Jira issue keys like HRZ-NNNNN, HCMDEV-NNNNN, FIDEV-NNNNN, SCZ-NNNNN, GEC-NNNNN.
---

# IFS Jira Reader

This skill provides the workflow for reading IFS Jira tickets to gather all context needed for defect investigation: issue details, reported version (to determine the release track), attachments, comments, and linked issues.

## Jira Site Configuration

- **Cloud ID / Site URL**: `ifsdev.atlassian.net`
- **Ticket format**: Just the Jira key (e.g. `HRZ-20473`), not the full URL
- **Full URL pattern**: `https://ifsdev.atlassian.net/browse/<issue-key>`

All MCP tool calls use `cloudId: "ifsdev.atlassian.net"`.

## Reading a Jira Ticket — Full Workflow

### Step 1: Fetch issue details

Use `mcp__atlassian__getJiraIssue` to retrieve the ticket:

```
cloudId: "ifsdev.atlassian.net"
issueIdOrKey: "<issue-key>"
responseContentFormat: "markdown"
```

Extract from the response:
- **Summary** — one-line problem description
- **Description** — full problem statement, reproduction steps
- **Status** — current workflow state
- **Priority** — severity level
- **Issue Type** — Bug, Task, Sub-task, etc.
- **Components** — affected IFS components
- **Labels** — categorization tags
- **Reported Version (Affects Version/s)** — determines the release track the customer reported against (see version mapping below)
- **IFS Planned Versions** — lists which release tracks need the fix; each planned version requires its own branch and PR
- **Fix Version/s** — target release for the fix
- **Attachments** — file metadata (names, sizes, types)
- **Linked Issues** — related tickets (swarming issues, parent tasks, duplicates)

### Step 2: Determine the release track

The **Reported Version** (Affects Version/s) field contains a version string like `24.1.2`, `25.2.0`, etc. The first two numbers determine the track:

| Version prefix | Track | Directory |
|---------------|-------|-----------|
| `24.1.x` | 24R1 | `24R1/` |
| `24.2.x` | 24R2 | `24R2/` |
| `25.1.x` | 25R1 | `25R1/` |
| `25.2.x` | 25R2 | `25R2/` |
| `26.1.x` | 26R1 | `26R1/` |
| `26.2.x` | 26R2 | `26R2/` |
| `27.1.x` | 27R1 | `IFSCloud-master/` |

**Rule**: Take the first number as the year (`YY`) and the second number as the half (`R`). Format as `YYR<half>`. For example, version `24.1.2` → year `24`, half `1` → track **24R1**.

If the version maps to the current master release (currently 27R1), the directory is `IFSCloud-master/`.

**Unsupported/legacy versions**: If the Reported Version shows a legacy product like `IFSAPP10-Core`, `Apps10`, or any version not in the table above, it refers to a product IFS no longer supports. In this case, **ignore the Reported Version** for track determination and instead use the **earliest IFS Planned Version** as the investigation track.

### Step 3: Read comments

Comments contain valuable investigation context — developer notes, customer clarifications, reproduction details, workaround suggestions, and root cause analysis from swarming sessions.

The `getJiraIssue` response includes comments in the fields. Read through **all comments** chronologically to understand:
- Additional reproduction steps from the customer
- Findings from other developers who investigated
- Workarounds or temporary fixes already applied
- Scope clarifications or priority changes

### Step 4: Read linked issues

Check the `issuelinks` field in the response for:
- **Swarming issues** — collaborative investigation tickets
- **Supplementary issues** — related defects or follow-ups
- **Parent/sub-task** relationships — broader task context
- **Duplicates** — earlier reports of the same issue

**Fetch every linked issue** using `getJiraIssue` with the same parameters (`cloudId`, `responseContentFormat: "markdown"`). Read their descriptions, comments, and attachments — linked issues often contain root cause analysis, additional reproduction steps, or partial fixes from prior investigation that are critical to understanding the full picture.

### Step 5: Download, convert, and read attachments

Attachments often contain critical evidence: Word specification documents, screenshots, error logs, stack traces, reproduction recordings, or data exports.

**Recommended — download + convert in one step:**

```bash
python .cursor/skills/ifs-jira-reader/scripts/process_jira_attachments.py <issue-key>
```

This writes to `docs/<issue-key>/attachments/`:

| Path | Contents |
|------|----------|
| `originals/` | Downloaded files as uploaded to Jira |
| `converted/` | Markdown converted from Word (`.docx`, `.doc`) |
| `media/` | Images/media extracted from Word docs |
| `ATTACHMENTS.md` | Index — **read this first** |

**Word documents:** Agents cannot reliably read `.docx`/`.doc` binaries directly. The script converts them to `.md` and embeds or links extracted images. Install optional deps for best results:

```bash
pip install -r .cursor/skills/ifs-jira-reader/scripts/requirements.txt
```

Legacy `.doc` files use `pandoc` when available; otherwise a stub Markdown file points to the original.

**For image attachments** (PNG, JPG, GIF):
Read directly from `originals/` or via image references in converted Markdown / `ATTACHMENTS.md`.

**For downloadable attachments** (logs, CSVs, text files, PDFs):
Either use the process script above, or download only:

```bash
python .cursor/skills/ifs-jira-reader/scripts/download_attachments.py <issue-key>
```

**Prerequisites for download scripts:**
- `JIRA_USER_EMAIL` environment variable set
- `JIRA_API_TOKEN` environment variable set
- Site defaults to `https://ifsdev.atlassian.net` (override with `JIRA_SITE_URL` if needed)

**Custom output directory:**
```bash
python .cursor/skills/ifs-jira-reader/scripts/process_jira_attachments.py <issue-key> --output-dir docs/<issue-key>/attachments
```

After processing, read each attachment via the path in `ATTACHMENTS.md`:
- **Converted Word** — Read `converted/*.md` (includes embedded media references)
- **Text/log files** — Read directly for error messages and stack traces
- **Images** — Read with the Read tool (supports PNG, JPG)
- **PDFs** — Read with the Read tool using the `pages` parameter
- **CSV/Excel** — Read for data patterns related to the defect
- **Video** — Use path from index; inspect manually if needed for reproduction

## Jira Ticket ID Prefixes

| Prefix | Area |
|--------|------|
| `HRZ-` | HR/Payroll (Horizon) |
| `HCMDEV-` | HCM Development |
| `FIDEV-` | Finance Development |
| `SCZ-` | Supply Chain |
| `GEC-` | General/Enterprise Core |

## Quick Reference — MCP Tool Calls

**Get issue details:**
```
mcp__atlassian__getJiraIssue
  cloudId: "ifsdev.atlassian.net"
  issueIdOrKey: "HRZ-20473"
  responseContentFormat: "markdown"
```

**Search related issues by JQL:**
```
mcp__atlassian__searchJiraIssuesUsingJql
  cloudId: "ifsdev.atlassian.net"
  jql: "issue in linkedIssues('HRZ-20473')"
  responseContentFormat: "markdown"
```

**Search by component and version:**
```
mcp__atlassian__searchJiraIssuesUsingJql
  cloudId: "ifsdev.atlassian.net"
  jql: "project = HRZ AND component = person AND affectedVersion = '24.1.2'"
  responseContentFormat: "markdown"
```

## Additional Resources

### Scripts

- **`scripts/process_jira_attachments.py`** — Download attachments, convert Word to Markdown, extract media, write `ATTACHMENTS.md`. Preferred for defect analysis.
- **`scripts/download_attachments.py`** — Download-only (stdlib). Writes to `./jira-attachments/<issue-key>/`.
- **`scripts/requirements.txt`** — Optional `mammoth` for richer Word → Markdown conversion.
