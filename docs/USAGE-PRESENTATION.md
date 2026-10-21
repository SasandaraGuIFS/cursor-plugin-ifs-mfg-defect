---
marp: true
theme: default
paginate: true
size: 16:9
title: Using the IFS Mfg Defect Analyzer — step by step
author: IFS R&D Manufacturing
footer: "IFS R&D — Internal · /mfg-defect"
---

<!--
Build this file to .pptx with one of:
  marp docs/USAGE-PRESENTATION.md -o docs/USAGE-PRESENTATION.pptx
  pandoc docs/USAGE-PRESENTATION.md -o docs/USAGE-PRESENTATION.pptx
  (or ask the agent to run the pptx skill on it)

Slide separators are `---` on their own line.
-->

# Using `/mfg-defect`

**A step-by-step walkthrough — from Jira link to merged fix**

v0.1.0 · IFS R&D Manufacturing

---

## The one command you need to remember

In any Cursor chat on an IFS workspace:

```
/mfg-defect MFZ-31273
```

That's it. The plugin owns the next 8 steps.

<!--
If the chat is already named MFZ-31273, it resumes from the first unfinished
gate instead of starting over.
-->

---

## What the plugin can do (capability map)

| Area | Capability |
| --- | --- |
| **Jira (read-only)** | Fetch issue, download + convert attachments, pull similar tickets |
| **Explain** | Produce plain-English summary + real-world example (no LU names) |
| **Decide** | Verdict: product defect vs intended design (with proof) |
| **Recreate** | Author + run a from-scratch Script-A-Rest with bug asserts |
| **Investigate** | Trace call chain across `.plsql`, `.plsvc`, `.projection`, `.client` |
| **Review** | A-Z code review on every proposed file before it hits disk |
| **Deploy** | Fast codegen + deploy to a MASTER CMB |
| **Verify fix** | Unit tests (`.pltst`) + second assert set on the recreate SAR |
| **RCA draft** | Theme / sub-theme / Introduced In / preventive actions |
| **Matrix** | Standalone fix-flow SAR under `docs/<KEY>/sar/` |
| **Release notes** | Customer-facing draft, past tense |
| **Commit** | 27R1 bugfix branch (manual push) |
| **Backport** | 26R2 / 26R1 / 25R2 / 25R1 / 24R2 with track history comments |

Everything a planner-safe. **Never writes Jira.**

---

## What it will NOT do

- **Post comments, RCA fields, release notes, or labels to Jira.** You always get a draft to paste.
- **Edit source files before Step 5b.** Draft + code review come first.
- **Deploy to anything other than your chosen MASTER CMB** (no auto-promotion).
- **Push to Bitbucket** — you push the branch yourself.
- **Create or merge PRs** — stays in your hands.
- **Guess.** If evidence is missing it stops and asks.

---

## Step 1 — Attachments and plain explanation

**You:**
```
/mfg-defect MFZ-31273
```

**The agent:**
1. Renames the chat to `MFZ-31273`.
2. Calls `getJiraIssue` (markdown), reads summary, description, comments.
3. Runs `process_jira_attachments.py MFZ-31273`:
   - downloads all attachments to `docs/MFZ-31273/attachments/`
   - converts PDFs / Office / HTML to markdown under `converted/`
   - writes `ATTACHMENTS.md` as an index.
4. Writes **two short blocks** in chat:
   - **What is going on** — a few plain sentences.
   - **Real-world example** — one concrete planner / operator scenario.

**You:** read and confirm the behaviour matches the ticket.

---

## Step 2 — Similar Jira

**The agent** searches Jira with keywords + component + Closed/Resolved + same error / entity.

**Output:** short table of up to ~5 similar tickets with status, resolution, link.

If no hits, it says so and moves on. Confluence is intentionally skipped (noisy).

**You:** glance at the table; mention if any of them look like the same bug — the agent will fold that into the verdict.

---

## Step 3 — Verdict: product defect or intended design

**The agent** reads:
- functional docs for the reported version (`docs.ifs.com/.../YYrX/`),
- the attachments it processed,
- the LU / page / projection / PL/SQL in your workspace (via `ifs-file-traverse` map).

**Output in chat and `docs/<KEY>/analysis.md`:**

- **Verdict** — `Product defect` or `Intended design` (or `Config/Data only` if proven).
- **Proof** — numbered facts; each is a doc URL or `file:lines` citation.
- **Gaps** — what's still unknown if confidence is not high.

**You:** confirm the verdict so the agent branches correctly.

---

## Step 4a — If intended design: WAD comment draft

The agent writes a paste-ready **Working As Designed** comment in chat and in `analysis.md`:

- Opens with "This is intended behaviour."
- Links the doc page that defines it.
- Cites `file:lines` for the implementing code.
- Explains why *this* ticket matches.

**You:** paste it into Jira yourself (plugin never writes Jira).

Flow stops here for intended-design tickets.

---

## Step 4c — Recreate SAR (product-defect path)

The agent authors **one** MKD under `docs/MFZ-31273/recreate/`:

- From-scratch data (no reliance on an existing part / order).
- Compact bug-id keys (`CO_1`, `SO_1` ...).
- Prefers existing REST utils; local `recreate/util/` only when needed.
- **Bug-proving asserts** on the records that show the defect.

Then it runs ScriptARest on **one** MASTER CMB:

- Prefers **MASTER DEV CMB** (`ifsmasterbnddevcmb.rnd.ifsdevworld.com`).
- Falls back to **MASTER DEP CMB**.
- As `alain` / `alain`. `ServerUrl` is origin only.

Fixes harness issues and re-runs until **bug asserts pass**. That is the recreate.

---

## Step 4b — Functional investigation summary

**One paragraph** in planner / operator language — what was looked at, what the user does, what they expected, what actually happens, and that the behaviour was reproduced.

No LU names, no file paths, no SQL. Pure functional story.

**You:** forward this to functional / support if they ask "did you reproduce it?"

---

## Step 5 — Investigate and draft the fix

The agent:

1. Traces the call chain across `.plsql`, `.plsvc`, `.projection`, `.client`.
2. Uses git history if the regression commit matters.
3. States **the exact fault** and **why it fails**.
4. Drafts the fix — does **not** apply it.
5. Runs **`ifs-code-review`** on every proposed file (A-Z checklist).

**Output in chat:** the draft diff + the code review verdict side-by-side.

**You:** approve the draft, or ask for revisions. Nothing is written to disk yet.

---

## Step 5b — Apply, deploy, verify

Once you approve, the agent:

1. **Applies** the drafted change in the workspace.
2. **Deploys** via `ifs-codegen` — `.plsql` fast path uses `fast-deploy-plsql.ps1`.
3. **Runs unit tests** — each changed `.plsql` / `.plsvc`'s `.pltst` sibling. Writes `none` in `analysis.md` if no `.pltst` exists.
4. **Adds a second assert set** to the recreate SAR that proves the *correct* behaviour.
5. **Re-runs** the SAR until **fix asserts pass**.

Any failure (compile, unit test, fix assert) → it stops, investigates, revises, retries. Does not treat warnings as success.

---

## Step 6 — RCA draft (`jira-rca`)

After the fix verifies, the agent (or the `jira-rca` subagent) drafts:

- **Theme / sub-theme** — picked from the IFS RCA theme catalogue.
- **Introduced In** — from `git blame` + `git log` on the changed lines.
- **Root cause narrative** — ≤ 3 sentences, mechanism-first.
- **Preventive actions** — concrete, each one assignable.

Written to `docs/<KEY>/analysis.md`. **You** paste it into the Jira RCA tab.

---

## Step 7 — Fix-flow test matrix + SAR

The agent:

1. Runs `connected_sar_analyzers.py select --files <changed.plsql>` to discover affected flows (JSON evidence with `file:line`).
2. Dedups against existing `inttst` scripts — marks each as `Covered in inttst` (skip / reuse).
3. Writes `docs/<KEY>/TEST-MATRIX.md` with `ID / flow / Must-Should / Kind / preconditions / expected / inttst decision`.
4. Authors gap / fix-specific cases under `docs/<KEY>/sar/`:
   - `RunCoreMatrix.mkd`
   - `util/`
   - `tests/`
5. Runs the matrix until green.
6. Records `docs/<KEY>/sar/RESULTS.md`.

**You:** attach `TEST-MATRIX.md` + `RESULTS.md` to the Jira as proof.

---

## Step 8 — Release notes draft

Follows `ifs-jira-release-notes`:

- Customer-facing prose, **past tense**.
- No bullets, no ticket links, no names.
- Does not copy the RCA narrative.
- Notes if `ExcludeFromSUReport` is justified.

**You:** paste it into the Jira **Release Notes** field. Done.

---

## Optional — commit + backport

After the fix is proven on master (27R1):

```
"commit the master fix"           → ifs-master-commit
"backport MFZ-31273 to 26R2"      → ifs-track-backport
```

- `ifs-master-commit` — creates `bugfix/MFZ-31273` from `origin/master`, commits only the files that fix this Jira, runs an A-Z review, pushes the branch (no PR created).
- `ifs-track-backport` — same change into `bugfix/MFZ-31273-26R2`, with track-specific history comments, deploys to **26R2 DEV CMB**, re-runs the recreate SAR with fix asserts.

Both stay out of Jira. You create the Bitbucket PR yourself.

---

## Artifacts that land on disk

Everything is organised under `docs/<KEY>/` in the workspace:

```
docs/MFZ-31273/
  analysis.md                       Resume + outcomes log
  attachments/                      Downloaded Jira attachments
  attachments/converted/            Markdown-converted PDFs / Office
  recreate/
    RecreateOpTransactionCost...mkd Bug asserts + fix asserts
    last-run.txt · last-run-fix.txt ScriptARest console output
  sar/
    RunCoreMatrix.mkd               Entry point for Step 7
    tests/CASE01_...mkd             Fix-flow cases
    util/                           Local helpers if any
    RESULTS.md                      Pass/fail per case
  TEST-MATRIX.md                    Flows + inttst decisions
```

Everything is versionable, reviewable, and attachable to Jira.

---

## Typical timeline

| Phase | Time (first time) | Time (resume) |
| --- | --- | --- |
| Step 1 (fetch + explain) | 2-3 min | 10 s |
| Step 3 (verdict) | 5-10 min | 1 min |
| Step 4c (recreate SAR) | 15-30 min | 5 min re-run |
| Step 5 + 5b (fix + verify) | 20-45 min | - |
| Step 6 (RCA) | 3-5 min | - |
| Step 7 (matrix + SAR) | 20-40 min | 5 min re-run |
| Step 8 (release notes) | 2 min | - |

**End-to-end on a fresh MFZ:** typically **1-2 hours of agent time** for a one-package fix. Resuming a defect you already recreated usually completes in **30 min**.

---

## Resume semantics

If `docs/MFZ-31273/analysis.md` exists, the agent:

1. Reads the file.
2. Scans the checkbox list at the top.
3. Jumps to the first unfinished gate.
4. Continues until the next decision point.

Safe to:
- Close Cursor halfway and reopen tomorrow.
- Switch laptops (push `docs/MFZ-31273/` to a feature branch).
- Hand the ticket to a colleague — they just run `/mfg-defect MFZ-31273`.

---

## Guard-rails you can trust

- **Never writes Jira** — every RCA, comment, release note is a draft.
- **No source edit before Step 5b** — code review always runs first.
- **One MASTER CMB per ticket** — no cross-environment confusion.
- **ScriptARest `ServerUrl` is origin only** — no URL drift.
- **Deploy = `VALID` + no `USER_ERRORS`** — warnings are not success.
- **Fix assert failure = stop and investigate** — never "mostly passing".
- **Env data per workspace** — plugin ships a fallback, your repo stays source of truth.

---

## When something goes wrong

| Symptom | What the agent does |
| --- | --- |
| Jira fetch 403 | Reports and asks you to approve Atlassian MCP. |
| Attachment conversion fails | Logs the file in `ATTACHMENTS.md` as `(unconverted)` and continues. |
| Recreate SAR red | Classifies: harness vs data vs bug. Fixes harness, retries up to N. |
| Compile `USER_ERRORS` | Shows the error, does **not** advance. Asks for direction. |
| Unit test fails | Investigates: stale `.tst`? source not deployed? Fixes and retries. |
| Fix asserts fail | Reverts "done" state. Revises the patch, redeploys, re-runs. |
| 26R2 track differs | Backport skill flags the merge conflict and asks for review. |

In every case: evidence first, draft second, apply third.

---

## Try it on a tiny ticket first

Good first-time pick:

- A ticket you have already recreated manually.
- A one-package fix with a clear bug.
- A Master-track issue (27R1), not an old backport.

Run:

```
/mfg-defect MFZ-xxxxx
```

Watch the Step 1 explanation. If it matches your mental model of the bug, let it continue. If not, correct it before it builds the recreate SAR.

---

## Cheat sheet

| Need | Say |
| --- | --- |
| Start a defect | `/mfg-defect MFZ-xxxxx` |
| Resume an in-progress defect | `/mfg-defect MFZ-xxxxx` (same chat or new) |
| Re-run the recreate SAR only | "re-run the recreate SAR" |
| Add a scenario to Step 7 | "add scenario: planner releases a serial-tracked COMP with ..." |
| Draft the WAD comment and stop | "treat this as intended design and draft the comment" |
| Commit the master fix | "commit the master fix" |
| Backport to 26R2 | "backport MFZ-xxxxx to 26R2" |

---

## Thank you

**One command, eight steps, zero Jira writes.**

```
/mfg-defect MFZ-xxxxx
```

- Repo: <https://github.com/SasandaraGuIFS/cursor-plugin-ifs-mfg-defect>
- Install: Cursor Settings > Plugins > Add from git → paste the URL above
- Questions: open a [GitHub Issue](https://github.com/SasandaraGuIFS/cursor-plugin-ifs-mfg-defect/issues)
