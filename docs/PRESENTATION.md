---
marp: true
theme: default
paginate: true
size: 16:9
title: IFS Manufacturing Defect Analyzer — Cursor plugin
author: IFS R&D Manufacturing
footer: "IFS R&D — Internal"
---

<!--
How to turn this file into a PPTX:

  # Option A — Marp CLI (recommended, keeps slides styled)
  npm i -g @marp-team/marp-cli
  marp docs/PRESENTATION.md -o docs/PRESENTATION.pptx

  # Option B — Pandoc
  pandoc docs/PRESENTATION.md -o docs/PRESENTATION.pptx

  # Option C — Cursor "pptx" skill
  Open this file and ask the agent to generate a .pptx using the pptx skill.

Slide separators are `---` on their own line.
Speaker notes go in HTML comments right under the slide title.
-->

# IFS Manufacturing Defect Analyzer

**A Cursor plugin for end-to-end MFZ-\* defect handling**

v0.1.0 · October 2026 · IFS R&D Manufacturing

<!--
Opening slide. Say: this is a Cursor plugin that packages the manufacturing
defect analyzer flow so the whole team can install it in one click.
-->

---

## Why this plugin

- Manufacturing defects (MFZ-\*) follow the **same 8-step flow** every time.
- Today it lives in one developer's workspace as loose skills + scripts + prompts.
- Teammates re-invent recreate SARs, miss RCA fields, forget release notes.
- **Goal:** one `/mfg-defect <KEY>` command, same quality, zero setup drift.

<!--
Pain: inconsistent recreate quality, missing RCA, release notes forgotten,
"what skill did you use?" questions. We've already proved the flow on
MFZ-30650, MFZ-31069, MFZ-31273 — now ship it.
-->

---

## What it does

A Cursor **slash command + 14 bundled skills** that drive one defect from Jira link to merged fix:

> Fetch Jira → plain explanation → **from-scratch recreate SAR with bug asserts** → investigate + draft fix + A-Z code review → deploy + unit tests + **fix asserts** → RCA draft → standalone fix-flow SAR matrix → release notes draft.

**Never writes to Jira.** All text is drafted in chat and in `docs/<KEY>/analysis.md`.

<!--
"Never writes Jira" is a hard product rule — it's why the flow is safe to
install for the whole team without approval loops.
-->

---

## The 8-step flow

1. **Attachments + simple explanation** — fetch Jira, process attachments, write 2 short blocks.
2. **Similar Jira** — quick duplicates scan (no Confluence).
3. **Docs + code proof** — verdict: product defect **or** intended design.
4. **Branch** — WAD comment draft **or** recreate SAR with bug asserts.
5. **Investigate + draft fix** — A-Z code review before anything is applied.
5b. **Apply + deploy + unit tests + fix asserts** — proves the fix.
6. **RCA draft** — theme, sub-theme, Introduced In, preventive actions.
7. **Test matrix + standalone SAR** — fix-flow coverage under `docs/<KEY>/sar/`.
8. **Release notes draft** — customer-facing, past tense.

---

## Hard rules

- **Rename the chat to the Jira key** as the first action.
- **Never write Jira** — RCA, comments, release notes, labels are *drafts only*.
- **Recreate SAR runs same-chat** — no second-chat handoff.
- **Recreate on one MASTER CMB** — prefer `MASTER DEV CMB`, fall back to `MASTER DEP CMB`, as `alain`/`alain`.
- **ScriptARest `ServerUrl` is origin only** — no `/main/ifsapplications/web/`.
- **No source changes before Step 5b** — not even "small" ones.
- **Resume by reading `docs/<KEY>/analysis.md`** — don't restart finished steps.

<!--
These rules survive every re-prompt. They're the main thing that gets lost
when a developer "just does it manually".
-->

---

## What's in the box

```
.cursor-plugin/plugin.json      Cursor manifest
.claude-plugin/plugin.json      Claude Code manifest
.claude-plugin/marketplace.json Marketplace entry
plugin.json                     agent-plugins.org manifest

commands/mfg-defect.md          /mfg-defect <JIRA-KEY>

skills/   14 skills (see next slide)
shared/   docs/ + scripts/ (env + helpers)
tools/    verify-links.ps1, verify-skills.py, package.ps1
dist/     ifs-mfg-defect-<version>.zip
```

**Size:** ~146 KB zipped. Pure skills + prompts + helper scripts — no new MCP server.

---

## 14 bundled skills

| Skill | Role |
| --- | --- |
| `ifs-mfg-defect-analysis` | Orchestrator (Steps 1-8) |
| `ifs-jira-reader` | Step 1 Jira fetch + attachments |
| `ifs-codegen` | Step 5b codegen + deploy (`fast-deploy-plsql.ps1`) |
| `ifs-code-review` | Step 5 pre-apply A-Z review |
| `ifs-plsql-patterns` | PL/SQL CRUD / state-machine patterns |
| `ifs-test-writing` | `.pltst` discovery for Step 5b |
| `ifs-history-comments` | YYMMDD history-line placement |
| `ifs-sar-generator` | Recreate + fix SAR authoring rules |
| `ifs-connected-sar-selector` | Step 7 flow discovery analyzers |
| `ifs-standalone-fix-sar` | Step 7 matrix + runner |
| `ifs-jira-rca` | Step 6 RCA draft |
| `ifs-jira-release-notes` | Step 8 release notes draft |
| `ifs-master-commit` | 27R1 commit flow after fix |
| `ifs-track-backport` | Backport to 26R2 / 26R1 / 25R2 / ... |

---

## Prerequisites

**MCP servers** (install from Cursor Settings > MCP):

| Purpose | MCP namespace |
| --- | --- |
| Jira read + attachments | `user-Atlassian-MCP-Server` |
| Database | `user-sqlcl` |
| IFS codegen / deploy / live DB | `user-ifs-f1-codegen-dev` |
| Browser verification (optional) | `user-Playwright-MCP-Server` |
| PR / branch (optional) | `user-Bitbucket-MCP-Server` |

**Runtime:** Python 3.10+ on PATH, PowerShell 5.1+ or 7+, SQLcl with named connections (`MASTER DEV CMB`, `MASTER DEP CMB`, ...).

---

## Install — option 1 (git)

In Cursor:

**Settings > Plugins > Add plugin from git**

```
https://github.com/SasandaraGuIFS/cursor-plugin-ifs-mfg-defect.git
```

Cursor clones under `%USERPROFILE%\.cursor\plugins\cache\...` and auto-registers every skill and command. Updates are a single click.

<!--
This is the recommended path. Updates ship by pushing a new tag.
-->

---

## Install — option 2 (zip)

1. Download `ifs-mfg-defect-<version>.zip` from the [GitHub release](https://github.com/SasandaraGuIFS/cursor-plugin-ifs-mfg-defect/releases).
2. Unzip into `%USERPROFILE%\.cursor\plugins\local\ifs-mfg-defect\`.
3. Restart Cursor.

Air-gapped laptops, offline sites, or quick trials.

---

## Per-workspace setup (one-time)

Each IFS workspace repo needs two files the skills read directly:

```powershell
Copy-Item <plugin>\shared\docs\bnd-environment-urls.md         <ifs-workspace>\docs\
Copy-Item <plugin>\shared\docs\bnd-environment-connections.json <ifs-workspace>\docs\
```

These contain Aurena URLs, landing pages, SQLcl connection names, JDBC hosts, and env IDs for MASTER / 27R1 / 26R2 / 26R1 / 25R2 / 25R1 / 24R2. They're **per-track data**, so they live in the workspace, not the plugin.

---

## Usage

In a Cursor chat on your IFS workspace:

```
/mfg-defect MFZ-31273
```

The agent will:

1. Rename this chat to `MFZ-31273`.
2. Run Step 1 (fetch Jira + attachments, write the plain explanation + example).
3. Progress through Steps 2 → 8, stopping only when it needs a decision from you.

If `docs/MFZ-31273/analysis.md` already exists, it **resumes** at the first unfinished gate — safe to re-run.

---

## Step 1 — Attachments + simple explanation

- Reads the Jira with `getJiraIssue` (markdown format).
- Runs `shared/scripts/process_jira_attachments.py <KEY>`:
  - downloads all attachments to `docs/<KEY>/attachments/`,
  - converts PDFs / Office docs to markdown under `converted/`,
  - produces `ATTACHMENTS.md` index.
- Writes **two short blocks** anyone can understand:
  - **What is going on** — a few sentences, user-centric, no LU names.
  - **Real-world example** — one concrete planner / operator scenario.

<!--
No stack traces, no LU names, no table dumps on this step. Keep it functional.
-->

---

## Step 3 — Verdict: product defect or intended design

Gather **functional docs** + **source code** + **attachments**, then write:

- **Verdict** — Product defect / Intended design / Config-only.
- **Proof** — numbered facts, each a doc URL or `file:lines` citation.
- **Gaps** — what is still missing if confidence is not high.

Then branch:

- **Intended design** → draft a paste-ready WAD comment (chat only).
- **Product defect** → start Step 4c recreate SAR.

---

## Step 4c — Recreate SAR with bug asserts

- Author **one MKD** under `docs/<KEY>/recreate/` — never under `inttst/`.
- From-scratch data, compact bug-id keys, prefers existing REST utils.
- **Bug-proving asserts** on the records that show the defect.
- Run ScriptARest on **one** MASTER CMB (DEV first, DEP fallback) as `alain`/`alain`.
- Fix harness issues until bug asserts pass — **that is the recreate**.
- No wait for user — continue to Step 4b (functional investigation summary).

---

## Step 5 — Investigate + draft fix + A-Z code review

- Full call-chain investigation across `.plsql`, `.plsvc`, `.projection`, `.client`.
- State **exact fault** and **why it fails**.
- Draft the fix — do **not** apply yet.
- **Run `ifs-code-review` on every proposed file** before showing it. Show the review alongside the draft.

<!--
This is the quality gate. Code review catches history-comment placement,
EBR naming, pattern violations, and missing error handling before the diff
hits disk.
-->

---

## Step 5b — Apply, deploy, verify

1. **Apply** the drafted change in the workspace.
2. **Deploy** via `ifs-codegen` — `.plsql` fast path uses [`fast-deploy-plsql.ps1`](shared/scripts/fast-deploy-plsql.ps1).
3. **Unit tests** — run each changed `.plsql` / `.plsvc`'s `.pltst` (if any exists).
4. **Fix asserts** — add a second assert set to the recreate SAR that proves the correct behaviour. Re-run on the same env until green.

Stop and investigate at any failure: compile error, failed unit test, failed fix assert. Do not treat deploy warnings as success.

---

## Step 6 — RCA draft (jira-rca)

Hands off to the **jira-rca** agent (if installed) or runs inline:

- Theme, sub-theme (from the jira-rca themes reference).
- **Introduced In** — git-blame + git-log on the changed lines.
- Brief root cause narrative — ≤ 3 sentences, mechanism-first.
- Preventive actions — concrete, assignable.

Written to `docs/<KEY>/analysis.md`. **Never written to Jira.**

---

## Step 7 — Test matrix + standalone fix SAR

- **Discover flows** with `connected_sar_analyzers.py select --files <changed.plsql>` — JSON evidence with `file:line` citations.
- **Dedup against inttst** — existing coverage is marked "Covered in inttst".
- Author **gap / fix-specific** cases under `docs/<KEY>/sar/`:
  - `RunCoreMatrix.mkd`, `util/`, `tests/`,
  - plus `docs/<KEY>/TEST-MATRIX.md` with Must/Should/Kind columns.
- Run until green — classify + fix harness issues per `ifs-standalone-fix-sar`.
- Record `docs/<KEY>/sar/RESULTS.md`.

---

## Step 8 — Release notes draft

Follows `ifs-jira-release-notes`:

- Customer-facing prose, **past tense**.
- No bullets, no ticket links, no names.
- Does **not** copy the RCA narrative.
- Noted in the draft if **ExcludeFromSUReport** is justified.

Draft shown in chat and recorded in `analysis.md`. **Not posted to Jira.**

---

## Build and verify (CI-friendly)

```powershell
# Link + script-reference sanity check
powershell -ExecutionPolicy Bypass -File tools\verify-links.ps1

# Frontmatter + name/description rules (Cursor Agent-Plugin validator)
py -3 tools\verify-skills.py

# Build release zip into dist/
powershell -ExecutionPolicy Bypass -File tools\package.ps1
```

All three exit 0 on success — wire them into a GitHub Actions workflow on every PR.

---

## Known limitations

- **Subagents are not bundled.** `jira-rca`, `standalone-fix-sar`, `track-backport`, `master-fix-commit`, `manufacturing-sar-agent`, `connected-sar-selector` — the skills still work without them (steps run inline in the same chat).
- **No new MCP server.** All tool calls go through MCPs you already have. If we later want one, the first candidate is a thin wrapper around the three helper scripts.
- **BnD env data is per-workspace.** `docs/bnd-environment-*` ships as a fallback but each IFS repo should keep its own copy for its tracks.

---

## Roadmap

- **v0.2** — bundle the five subagent `.md` files so RCA / standalone-fix-SAR / backport launch natively.
- **v0.3** — optional MCP server (`ifs-mfg-defect-helpers`) wrapping `process_jira_attachments.py`, `connected_sar_analyzers.py`, `fast-deploy-plsql.ps1` so Python/PowerShell is no longer required on each laptop.
- **v0.4** — GitHub Actions workflow publishing release zips automatically on `v*` tags.
- **v1.0** — adoption metrics: how many MFZ tickets handled end-to-end via `/mfg-defect`, pass rate on fix asserts, mean time from Jira to merged PR.

---

## Repo layout (reference)

```
cursor-plugin-ifs-mfg-defect/
  .cursor-plugin/plugin.json
  .claude-plugin/{plugin,marketplace}.json
  plugin.json
  README.md · CHANGELOG.md · LICENSE
  commands/mfg-defect.md
  skills/<14 skills>/SKILL.md (+ references/, scripts/, tools/, templates/)
  shared/
    docs/bnd-environment-urls.md
    docs/bnd-environment-connections.json
    scripts/fast-deploy-plsql.ps1
    scripts/connected_sar_analyzers.py
    scripts/process_jira_attachments.py
  tools/verify-links.ps1 · verify-skills.py · package.ps1
  dist/ifs-mfg-defect-<version>.zip
  docs/PRESENTATION.md   (this file)
```

---

## Thank you

**Try it today**

```
/mfg-defect MFZ-xxxxx
```

- Repo: <https://github.com/SasandaraGuIFS/cursor-plugin-ifs-mfg-defect>
- Issues / feature requests: use the repo's [GitHub Issues](https://github.com/SasandaraGuIFS/cursor-plugin-ifs-mfg-defect/issues)
- Rule you must follow: **never let the agent write Jira without your explicit yes**

Questions?
