---
name: mfg-defect
description: Run the IFS Manufacturing Defect Analyzer end-to-end for an MFZ-* Jira issue. Fetches Jira, writes a from-scratch recreate SAR, deploys the fix, verifies with fix asserts, drafts RCA, authors the fix-flow SAR matrix, and drafts release notes. Never writes Jira.
---

# /mfg-defect — IFS Manufacturing Defect Analyzer

Arguments: `$ARGUMENTS` — one IFS Jira key (e.g. `MFZ-31273`).

Follow the full protocol in the bundled skill `ifs-mfg-defect-analysis` end-to-end for the key in `$ARGUMENTS`.

Hard rules (restated for safety; the skill is the source of truth):

1. **Rename the chat to the Jira key** as the very first action, then start Step 1.
2. **Never write Jira.** Draft WAD comments, RCA fields, Release Notes, and tags in chat and in `docs/<KEY>/analysis.md` only. Do not ask to post them.
3. If `docs/<KEY>/analysis.md` already exists, read it first and resume at the first unfinished gate.
4. Recreate and fix verification run on **one** MASTER CMB (prefer MASTER DEV CMB, fall back to MASTER DEP CMB) as `alain`/`alain`. ScriptARest `ServerUrl` is origin only.
5. Do not apply source changes before Step 5b (after the proposed fix + `ifs-code-review` pass).

Begin now by reading `skills/ifs-mfg-defect-analysis/SKILL.md`, then execute Step 1 (fetch Jira, process attachments, write the two short blocks).
