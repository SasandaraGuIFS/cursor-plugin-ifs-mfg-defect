---
name: ifs-mfg-defect-analysis
description: Analyzes IFS Cloud manufacturing defects (shop order, shop material, DOP, MFZ tickets). Use when the user pastes an MFZ- Jira key, asks to run the manufacturing defect analyzer, or describes a shop-order / material-allocation / DOP bug. Attachments first, then a plain explanation plus real-world example; draft Jira text in chat only — never write Jira.
---

# IFS Manufacturing Defect Analyzer

Run this flow for **MFZ-** tickets and shop order / shop material / DOP issues. Do **not** use the generic `ifs-defect-analysis` protocol for those.

Read [ifs-jira-reader](../ifs-jira-reader/SKILL.md) for Jira fetch and track mapping. Trace map: [references/mfg-trace-map.md](references/mfg-trace-map.md). Resume template: [references/resume-template.md](references/resume-template.md). Recreate SAR (same chat): [references/recreate-sar.md](references/recreate-sar.md).

Keep this file in sync with `.cursor/skills/ifs-mfg-defect-analysis/SKILL.md`.

## Chat title (first action)

Before anything else once the Jira key is known:

1. Call `cursor-app-control.rename_chat` with `title` set to the issue key only (e.g. `MFZ-30650`) — uppercase, no summary or suffix.
2. Do not ask for confirmation. Do not mention the rename unless the tool fails.
3. If the key is not in the user message, read `docs/<KEY>/analysis.md` or ask for the key, then rename before Step 1.
4. If `rename_chat` is unavailable, tell the user once to rename this chat to the Jira key manually so it is searchable.

### Backfill previous chats

`rename_chat` only renames the **active** chat. To fix older mfg-defect chats, run (dry run first):

```bash
py -3 .cursor/skills/ifs-mfg-defect-analysis/scripts/rename_mfg_defect_chats.py
py -3 .cursor/skills/ifs-mfg-defect-analysis/scripts/rename_mfg_defect_chats.py --apply
```

The script scans agent transcripts for `ifs-mfg-defect-analysis` sessions, extracts the Jira key, and updates Cursor’s chat title databases. Restart or reload Cursor if titles do not refresh immediately.

## Hard rules

- **Rename the chat to the Jira key** as soon as the key is known (see above).
- **Never write Jira** (comment, RCA, Release Notes, tags). Draft WAD comments, RCA, and Release Notes in chat / `analysis.md` only. Do not ask to post them.
- **Do not guess.** If evidence is incomplete, ask and stop the branch.
- Never invent Jira tickets or SAR suites.
- Do not apply source-file changes until **Step 5b** (after the proposed fix and code review are shown).
- Deploy only to the MASTER CMB used to recreate the bug.
- Re-run a completed step only when the user asks.
- Recreate is **same-chat**. Author and run a from-scratch SAR with **bug-proving asserts** under `docs/<KEY>/recreate/`. Follow [references/recreate-sar.md](references/recreate-sar.md) plus manufacturing-sar-agent / ifs-sar-generator rules. Do not hand off a second chat. Do not use standalone-fix-sar or SAR-FDA for recreate.
- Run recreate on **one** MASTER CMB as `alain`/`alain` (prefer DEV, fall back to DEP). ScriptARest `ServerUrl` is origin only — no `/main/ifsapplications/web/`.
- Bug asserts passing **is** the recreate check. Do not wait for the user. After deploy, author and run a **separate Verify SAR** under `docs/<KEY>/recreate/` with fix asserts. Do not overwrite the Recreate MKD.
- Recreate and Verify SARs are not the Step 7 standalone fix suite (`docs/<KEY>/sar/`).
- **Do not** run master-commit (Step 9) or track-backport (Step 10) until the user confirms that git step. Draft files/tracks, ask, wait. Vague approval is not enough. Skip both if intended design. Skip 10 if Step 9 did not push or the user declined 9.

## Resume (every ticket)

1. If `docs/<KEY>/analysis.md` exists, **read it first** and resume at the first unfinished gate.
2. After each step, update that file (outcomes + checkboxes). Copy the skeleton from [references/resume-template.md](references/resume-template.md) on first run.
3. Recreate is proven by bug asserts. The fix is proven by the **Verify SAR** fix asserts. WAD comments, RCA, and Release Notes are drafts only — do not write Jira and do not ask.

## Flow

```
Fetch + attachments → plain explanation + example → similar Jira
  → docs + code proof → (WAD comment | from-scratch recreate SAR with bug asserts)
  → run ScriptARest on one MASTER CMB (prefer DEV, alain/alain) until bug asserts pass
  → functional investigation summary (1 paragraph)
  → investigate + draft fix + code review
  → apply + deploy → unit tests for changed files → run Verify SAR until fix asserts pass
  → (if deploy fails, unit tests fail, or fix asserts fail: investigate, retry)
  → jira-rca agent → test matrix + standalone SAR (ifs-standalone-fix-sar)
  → Release Notes draft
  → ask to commit 27R1 → (yes) master-fix-commit → ask to backport → (yes) track-backport
```

## Recreate sequence (mandatory)

Use this for **Step 4** (show the bug) and **Step 5b** (show the fix). Follow [references/recreate-sar.md](references/recreate-sar.md).

1. Author a from-scratch SAR under `docs/<KEY>/recreate/` (never `inttst/`). Copy shape from `docs/MFZ-30650/recreate/RecreateIssuedPhantomCcr.mkd` and `docs/MFZ-31069/recreate/RecreateDuplicateMaterialLinesUpdateSupplyConfig.mkd` (`type: Recreate SAR`). Prefer existing REST utils; local `recreate/util/` only when needed. Compact bug-id keys.
2. **Assert the bug.** Query the records that show the defect, then Assert.
3. Run ScriptARest on **one** MASTER CMB as `alain`/`alain`. Prefer MASTER DEV CMB (`https://ifsmasterbnddevcmb.rnd.ifsdevworld.com`); if down, MASTER DEP CMB (`https://ifsmasterbnddepcmb.rnd.ifsdevworld.com`). `ServerUrl` is origin only — strip `/main/ifsapplications/web/`. Record the env in `analysis.md`.
4. Fix harness issues and re-run until 0 failed server calls **and** bug asserts pass. That is recreate. Do not wait. Continue to Step 4b.
5. **Step 5b:** keep the Recreate MKD unchanged. Author `Verify<ShortName>.mkd` that reuses the same setup (prefer a local `recreate/util/`) with **fix asserts**. Run it on the same env until those asserts pass.

---

### Step 1 — Attachments, then a simple explanation

**Before any analysis text:**

1. Fetch the issue (read-only): `getJiraIssue`, `cloudId: "ifsdev.atlassian.net"`, `responseContentFormat: "markdown"`. Read summary, description, comments, links, reported version.
2. Process attachments (prefer `.cursor` path; fall back to `.claude` if needed):

```bash
python .cursor/skills/ifs-jira-reader/scripts/process_jira_attachments.py <issue-key>
```

3. Read `docs/<KEY>/attachments/ATTACHMENTS.md`, `converted/*.md`, images, and logs.

**Then write only two short blocks** (anyone should understand them — no LU names, stack traces, or field dumps):

- **What is going on** — a few sentences: who is doing what, what they expected, what happens.
- **Real-world example** — one concrete factory / planner / operator scenario that matches the ticket.

Do not use the old Symptom / Affected Area / Reported RCA template.

---

### Step 2 — Similar Jira only

Search Jira (keywords, component, Closed/Resolved, same error or entity). Show a short table if hits exist; if none, say so. **Skip Confluence.**

---

### Step 3 — Docs + code proof (intended design vs product defect)

Gather evidence, then verdict. Do not propose a fix here.

**Docs** (summarise; do not paste large blocks):

- Functional docs for the reported version: `https://docs.ifs.com/ifsclouddocs/<YYrX>/lang/en/` — Explanation, Prerequisites, System Effects.
- Attachments already processed in Step 1.
- TechDocs only if needed to interpret framework behaviour.

**Code** in this workspace: the LU / page / projection / PL/SQL that implements the behaviour. Cite `file:lines`. Use [references/mfg-trace-map.md](references/mfg-trace-map.md).

**Output:**

- **Verdict:** Product defect **or** Intended design (Config / Data / Customisation only if evidence clearly shows that).
- **Proof:** numbered facts, each a doc URL or code citation.
- **Gaps:** what is still missing if confidence is not high.

---

### Step 4 — Branch on verdict

**Intended behaviour:** draft a paste-ready WAD comment in chat / `analysis.md`. Must include: this is intended behaviour; what the product is designed to do (doc URL); what the code does (`file:lines`); why this case matches. No speculation. **Do not** post it to Jira. **Do not** ask to post it.

**Product defect:** **Execute** the recreate sequence (do not only write a plan). Author and run the from-scratch SAR with bug asserts in **this chat**. When bug asserts pass, continue to Step 4b — do not wait for recreate confirmation.

---

### Step 4c — Recreate SAR (same chat)

Product-defect path only. Skip if intended design. Follow [references/recreate-sar.md](references/recreate-sar.md). Author with manufacturing-sar-agent / ifs-sar-generator rules. Do not hand off a second chat.

1. Author one MKD under `docs/<KEY>/recreate/` with from-scratch data **and bug-proving asserts** (never `inttst/`). Prefer existing SAR utils. Do not invent REST.
2. Run on one MASTER CMB (`alain`/`alain`; prefer DEV, fall back to DEP). `ServerUrl` origin only.
3. Fix the SAR and re-run until it is green (harness + bug asserts). Write created keys into `docs/<KEY>/analysis.md`.
4. Check `Recreate SAR authored` and `Recreate SAR green (bug asserts)` in `analysis.md`. Continue — do not wait.

---

### Step 4b — Functional investigation summary

Only after bug-proving asserts pass. Skip if intended design.

Write **one paragraph** that explains the investigation in **functional** language — how a planner or shop-floor user would describe it. Cover: what process was looked at, what the user does, what they expected, what actually happens, and that the behaviour was reproduced.

Do **not** include LU names, file paths, APIs, SQL, stack traces, or code citations. Technical detail belongs in Step 5.

Then continue to Step 5.

---

### Step 5 — Investigate and draft a fix

Only after the functional investigation summary.

1. Full investigation: LU, projection, client, PL/SQL call chain, git history if needed, [mfg-trace-map](references/mfg-trace-map.md).
2. State the exact fault and why it fails.
3. Draft the fix (do not apply). Follow `ifs-plsql-patterns` and `ifs-test-writing` where relevant.
4. **Before presenting**, read and run [ifs-code-review](../ifs-code-review/SKILL.md) on every proposed file. Show the review with the draft.

Then continue to Step 5b. Do not skip deploy-and-verify.

---

### Step 5b — Apply, deploy, verify (product-defect path)

Only after Step 5. Skip if intended design.

1. **Environment**
   - Reuse the Step 4 MASTER CMB (prefer DEV, fallback DEP) and `alain`/`alain`.
   - ScriptARest `ServerUrl` origin only. SQLcl name `MASTER DEV CMB` or `MASTER DEP CMB` from `docs/bnd-environment-connections.json`. Do not invent hosts.

2. **Apply** the proposed source change in the workspace (the draft from Step 5).

3. **Deploy** using [ifs-codegen](../ifs-codegen/SKILL.md):
   - `.plsql` → generate/deploy package spec+body. Prefer [`tools/fast-deploy-plsql.ps1`](../ifs-codegen/tools/fast-deploy-plsql.ps1) with **this env’s** connection — do not use the baked-in 26R1 URL.
   - Model files → generate, then deploy only `deployFiles` / the master script.
   - Treat compile as success only when objects are `VALID` and there are no `USER_ERRORS`. Ignore SQLcl Java warnings.

4. **If deploy fails** — do not continue. Investigate: `USER_ERRORS` / `ORA-` / `PLS-`, track mismatch (workspace vs target DB), missing JAR/SQLcl, wrong connection, annotation or deploy-order mistakes. Fix the deploy issue or the patch, then retry.

5. **Run unit tests for changed files** — only after objects are `VALID` and there are no `USER_ERRORS`.
   - Each Step 5b changed `.plsql` / `.plsvc` / `.pltst`. Deduplicate.
   - Map `source/<comp>/database/<Stem>.plsql` (or `.plsvc`) to `test/<comp>/database/<Stem>.pltst`. A changed `.pltst` is run as itself. Follow [ifs-test-writing](../ifs-test-writing/SKILL.md) for location only — do not author new tests in 5b.
   - If no `.pltst` exists: write `none` in `docs/<KEY>/analysis.md` and continue. Do not invent or generate tests here.
   - Run on the same recreate DB (never a default Master/26R1 host). Prefer ifs-f1-codegen `run_pltst_test` (`run_only` after generating/deploying `.tst` from the sibling `.entity` / `.utility` / `.enumeration`). If MCP is unavailable, use `%TEMP%\IFSLumos\pltst_deploy_and_run.ps1` with **this env’s** profiles JSON. Never deploy raw `.pltst` to SQLcl. Package name `{STEM}_TST` (e.g. `PART_SERIAL_CATALOG_TST`).
   - If tests fail: do not continue to fix-assert verify. Investigate (stale `.tst`, source not deployed, assertion vs fix, env mismatch). Fix patch or test, redeploy, re-run. Same stop rule as item 4.
   - If Step 5 already drafted `.pltst` changes: those files are in the apply/deploy set and must be generated/deployed/run here.

6. **Verify with a separate SAR:**
   - Keep `docs/<KEY>/recreate/Recreate<ShortName>.mkd` unchanged (bug asserts).
   - Author `docs/<KEY>/recreate/Verify<ShortName>.mkd` with the same setup and **fix asserts**. Prefer a shared `recreate/util/` so the two files do not duplicate the data chain.
   - Run the Verify SAR on the **same** MASTER CMB until fix asserts pass. If the env was wiped, re-run Verify as recovery seed.
   - Cover the primary failing path; add a second flow only if the ticket has two equally central paths.

7. **If fix asserts fail** — do not treat the fix as done. Investigate: wrong LU/method, patch not in the deployed `.api`/`.apy`, session/cache, data not matching recreate, secondary cause. Revise the draft, redeploy, re-run unit tests, then retry the Verify SAR.

8. Record env, deploy result, unit-test package / pass-fail counts / `none`, keys, and assert results in `docs/<KEY>/analysis.md`. Then continue to Step 6.

Fix asserts passing **is** the main-flow confirmation. Continue to Step 6 then Step 7 — do not wait.

---

### Step 6 — jira-rca agent

Product-defect path only. Skip if intended design.

After the root cause is identified (the drafted fix is required input):

1. Launch `Task` with `subagent_type: jira-rca`. Follow [ifs-jira-rca](../ifs-jira-rca/SKILL.md) for **draft content only** — skip that skill’s “ask to update Jira” / write steps.
2. Hand off: Jira key, investigation notes, drafted fix, git blame / Introduced In if known.
3. Show theme, sub-theme, Introduced In, brief root cause, preventive actions.
4. Show the RCA draft in chat and record it in `analysis.md`. **Do not** write Jira RCA fields. **Do not** ask to update Jira. Do not guess theme/sub-theme yourself (use the jira-rca agent output).

---

### Step 7 — Test matrix + SAR

Only after recreate **fix asserts** pass (Step 5b) and RCA is drafted (Step 6). Skip if intended design. Do not wait for a main-flow confirmation.

Follow [ifs-standalone-fix-sar](../ifs-standalone-fix-sar/SKILL.md) (agent: Standalone Fix-Flow SAR). Do **not** add files under `inttst/`. Do **not** auto-write `.pltst` unless asked.

**Discover flows** (inventory only — do not treat this as the suite to execute):

```powershell
py -3 .cursor/skills/ifs-connected-sar-selector/scripts/connected_sar_analyzers.py select --files <changed.plsql>
```

Cite only JSON `evidence[].file` + `evidence[].line`. If `candidates` is empty, run `area_map` for the component; never return an empty flow set silently. Related manufacturing rows: [mfg-trace-map](references/mfg-trace-map.md).

**Dedup, then author:** scan cited `inttst` scripts so existing flows are **Covered in inttst** (skip / reuse utils). Author **only gap / fix-specific** cases under `docs/<KEY>/sar/` (`RunCoreMatrix.mkd`, `util/`, `tests/`). Write `docs/<KEY>/TEST-MATRIX.md` (or ticket-local matrix name) **before** any new `.mkd`, with columns: ID, flow name, Must/Should, Kind, preconditions or SAR path, expected, notes, inttst decision.

**Run until green:** deploy DUT if needed; ScriptARest; classify and fix harness issues per `ifs-standalone-fix-sar`. Record `docs/<KEY>/sar/RESULTS.md` (newly automated vs skipped duplicates vs manual).

Optional: launch `Task` with `subagent_type: standalone-fix-sar` and hand off the Jira key, changed files, env, and matrix path. The Step 7 owner still updates `analysis.md`.

---

### Step 8 — Release Notes

After the matrix (product-defect path only). Follow [ifs-jira-release-notes](../ifs-jira-release-notes/SKILL.md) for **draft content only** — skip that skill’s “ask to update Jira” / write steps.

Customer-facing prose, past tense, no bullets, no ticket links, no names. Do not copy the RCA narrative. Show the draft in chat and record it in `analysis.md`. **Do not** write the Jira Release Notes field or Tags. **Do not** ask to update Jira. Optionally note in the draft if **ExcludeFromSUReport** would be justified.

Then continue to Step 9 — **ask**, do not commit yet.

---

### Step 9 — Master commit (user must confirm)

Product-defect path only. Skip if intended design.

Follow [ifs-master-commit](../ifs-master-commit/SKILL.md) (agent: `master-fix-commit`, Composer 2.5). **Do not** create Bitbucket PRs. **Do not** write Jira.

1. **Draft** the git step: Jira key, DUT file list from `docs/<KEY>/analysis.md` Step 5 (applied source only — not `docs/<KEY>/`, skills, or `.sar-fda`), proposed branch `bugfix/gunslk/27R1-<KEY>-<slug>`, commit subject `<KEY>: <Jira summary>`.
2. **Show** that draft in chat.
3. **Ask:** *Should I run master-commit for `<KEY>`? Reply **yes**, **no**, or **edit**.*
4. **Wait.** Unambiguous **yes** (or revised list after **edit**, then confirm again). `/commit-master-fix` in this conversation also counts as yes. “Looks good” / “proceed with the fix” is **not** yes.
5. **No** — skip Step 9 and Step 10. Record skipped in `analysis.md`.
6. On **yes**, launch `Task` with `subagent_type: master-fix-commit` (Composer 2.5). Hand off: Jira key, DUT paths from analysis.md. Record the wrap-up table in `analysis.md`.

Do not start Step 10 until Step 9 has pushed and GPT 5.6 review was not left blocking.

---

### Step 10 — Track backport (user must confirm)

Product-defect path only. Skip if intended design, if Step 9 did not push, or if the user declined Step 9.

Follow [ifs-track-backport](../ifs-track-backport/SKILL.md) (agent: `track-backport`). **Do not** create Bitbucket PRs. **Do not** write Jira.

1. **Draft** the git step: planned versions except 27R1 (newest first), proposed `bugfix/gunslk/<TRACK>-<KEY>-<slug>` branches, Verify SAR path (`docs/<KEY>/recreate/Verify*.mkd`).
2. **Show** that draft in chat.
3. **Ask:** *Should I run track-backport for `<KEY>`? Reply **yes**, **no**, or **edit**.*
4. **Wait.** Unambiguous **yes** (or revised track list after **edit**, then confirm again). `/apply-previous-tracks` in this conversation also counts as yes. Vague approval is **not** yes.
5. **No** — skip Step 10. Record skipped in `analysis.md`.
6. On **yes**, launch `Task` with `subagent_type: track-backport`. Hand off: Jira key, master commit/branch from Step 9. Record the wrap-up table in `analysis.md`.

## Jira

- Site / `cloudId`: `ifsdev.atlassian.net`
- `MFZ-` is manufacturing (same read path as other IFS keys).
