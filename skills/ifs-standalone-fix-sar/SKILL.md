---
name: ifs-standalone-fix-sar
description: >-
  Full process for standalone ScriptARest coverage of an IFS Cloud defect fix:
  discover affected and related flows, scan inttst to skip duplicates, author
  docs/<JIRA>/sar/ (not inttst), deploy DUT if needed, run ScriptARest, and
  self-correct harness issues until the core matrix is green. Use when the user
  pastes a Jira key, asks for a support-switch-style SAR matrix, standalone SAR
  under docs/, or automated run-until-green testing of a code fix.
---

# IFS Standalone Fix-Flow SAR

Read this skill **before** writing or running any `.mkd` for a Jira fix suite.
Companion agent: `.cursor/agents/standalone-fix-sar.agent.md`.

Reference implementation: `docs/MFZ-30650/sar/support-switch/`.

## When to use

- User wants testing **like MFZ-30650 support-switch**: matrix + standalone SAR + run.
- Jira key + local fix files; ship-gate / switch / optional API param / context cleanup.
- **Not** for placing preventive tests in `inttst` (use `test-automation` / manufacturing-sar-agent).
- **Not** for “which existing suites should I run” only (use `ifs-connected-sar-selector`).
- **Not** for chronic Jenkins SAR diagnosis (use SAR-FDA; that skill forbids editing `.mkd` to pass).

## Hard rules

1. Output only under `docs/<JIRA>/` and `docs/<JIRA>/sar/`. **Never** add files under `inttst/`.
2. **Dedup inttst** before authoring. Do not copy inttst test bodies into `docs/`.
3. Connected-SAR JSON is a **flow inventory**, not a list of suites to execute.
4. No Jira writes without explicit user confirmation of the exact change.
5. Do not change product PL/SQL/client to make a test pass. Fix SAR, setup, DUT deploy, flakes.
6. Run ScriptARest for core rows; do not skip unless env unreachable.
7. Use `py -3` for codegen/analyzers (not `python` on Windows).

## Pipeline

```
intake → select flows → dedup inttst → TEST-MATRIX → author SAR → deploy DUT
→ run one case → run rest → RunCoreMatrix → classify/fix (≤8) → RESULTS
```

---

## 1. Intake

- Jira: ifs-jira-reader / Atlassian MCP `getJiraIssue` (markdown). Comments + attachments.
- Git: files for the Jira vs `origin/master` (`git diff --name-only origin/master --` and ticket-tagged files).
- Fix narrative: what changed, default if omitted, what must still appear (chars, affected orders, supply lines).
- Environment: user-named BnD env, else **MASTER DEV CMB**.
  - URLs: `docs/bnd-environment-urls.md`
  - DB: `docs/bnd-environment-connections.json` (`sqlclConnectionName`, `dbHost`, `connectString`)
- Connect user: match recreate / existing `docs/<JIRA>/` SAR (`Connect alain` on DEV CMB if that is the peer). Do not invent MFU1 unless recreate uses it.

---

## 2. Affected and related flows (deterministic first)

From workspace root:

```powershell
py -3 .cursor/skills/ifs-connected-sar-selector/scripts/connected_sar_analyzers.py select --files <path1> <path2>
# fallback: .claude/skills/ifs-connected-sar-selector/scripts/connected_sar_analyzers.py
```

Or `--base origin/master --head HEAD`.

Then as needed:

```powershell
py -3 .cursor/skills/ifs-connected-sar-selector/scripts/connected_sar_analyzers.py impact_graph --package <PKG>_API --depth 1
py -3 .cursor/skills/ifs-connected-sar-selector/scripts/connected_sar_analyzers.py area_map --component <comp>
```

Treat `candidates[].evidence[].file` + `.line` as the only citeable proof.

- **Affected:** suites/utils that hit the changed package/svc.
- **Related:** impact_graph callers, same projection/page, same business object (CCR, DOP, SO, …).
- Extract **util paths** (`ReleaseConfigChangeReqUtil.mkd`, etc.) to Call from the new suite.

If `candidates` is empty: `area_map` + Grep peers. Never invent a flow with no evidence.

**Do not** run those inttst suites as the deliverable of this skill.

---

## 3. Dedup against inttst (mandatory before any new `.mkd`)

For each candidate flow:

1. Read the cited `.mkd` (suite, `tests/`, `util/`). Record page, actions, entities, asserts, Connect user.
2. Grep siblings for the same action, characteristic, supply type, or Jira-specific flag.
3. Classify:

| Decision | Meaning | What to author |
| --- | --- | --- |
| **skip** | Same actions + same expected outcome already in inttst (independent of the new fix) | Matrix row `Covered in inttst` + `path:line`. Call **utils** only if setup overlaps. |
| **new standalone** | inttst never asserts the new behavior (optional param, skip flag, session context, …) | Case under `docs/<JIRA>/sar/tests/` |
| **reuse** | inttst has setup/related path but not the new assert | Wrap/Call existing utils; add only the missing assert case |

Write the **coverage table** in `TEST-MATRIX.md` **before** creating test files:

```markdown
| Flow | inttst evidence | Decision |
| --- | --- | --- |
| Release CCR started supply | inttst/.../EditConfigWhenStartedSuppExistsSingleSiteEnabledDop.mkd:711 | skip / reuse utils |
| ExcludePhantomExplodeConflicts ON | (none) | new standalone |
```

---

## 4. Artifacts

| Path | Role |
| --- | --- |
| `docs/<JIRA>/TEST-MATRIX.md` or `docs/<JIRA>/SUPPORT-SWITCH-TEST-MATRIX.md` | Coverage + core/variant/manual |
| `docs/<JIRA>/sar/RunCoreMatrix.mkd` | `Connect` + `Call CatchError tests/...` |
| `docs/<JIRA>/sar/util/` | Setup wrap + inspect; Call inttst utils via relative paths |
| `docs/<JIRA>/sar/tests/` | One file per **new standalone** core row |
| `docs/<JIRA>/sar/RESULTS.md` | Env, keys, pass/fail, skipped duplicates |
| `docs/<JIRA>/sar/run-core-matrix.ps1` | ScriptARest wrapper |
| `docs/<JIRA>/sar/deploy-*.ps1` | Optional DUT deploy |

Templates: `.claude/skills/ifs-standalone-fix-sar/templates/` (also `.cursor/skills/ifs-standalone-fix-sar/templates/`).

Copy structure from `docs/MFZ-30650/sar/support-switch/` when the domain is CCR/config.

### Setup wrap pattern

Child `Call` does **not** leak locals. Recreate/setup must `Output` a JSON blob of keys; wrapper:

```cs
Call ../../../recreate/RecreateIssuedPhantomCcr.mkd Into setupData
Output setupData
```

Callers: `Call ../util/CreatePhantomCcrData.mkd Into setup` — **no** `With Json` unless a `{` block follows.

### Relative paths from `docs/<JIRA>/sar/tests/`

To inttst: `../../../../../inttst/test/inttst/<activity>/.../util/<Util>.mkd`

Count `..` from the **test file** directory. Verify with a path check before first run.

---

## 5. ScriptARest syntax (from MFZ-30650)

- `Call file.mkd With Json Into x` **must** be followed by `{` on the next lines. If there is no JSON, use `Call file.mkd Into x`.
- Do not pass OData objects through `ApplyJson` / util input. Refetch by ChangeId / OrderNo.
- `{%string}`, `{$number}`, `{#url}` — do not mix.
- Never use `>` or `>=` in Assert (engine crash). Use `== 0` / `!= 0` / ItemsCount as inttst peers do. Prefer `== "0"` vs `== 0` matching nearby peers.
- Fresh `RandomWithRange` data per case.
- Suite runner: `Call CatchError tests/Case.mkd`
- Background actions: `Delay` then assert (e.g. `Delay 60000`).
- Utils that need keys: `Output` a named JSON object from the child.

---

## 6. Deploy DUT

If ExecuteRelease (or similar) returns 400 `UNKNOWN_CONTENT` / `'Param' can not be mapped`:

1. Codegen the **projection** (and plsvc via generate on the model):

```powershell
py -3 .claude/skills/ifs-codegen/tools/ifs-codegen.py generate <workspace>/.../FooHandling.projection --json
# fallback: .cursor/skills/ifs-codegen/tools/ifs-codegen.py
```

2. Deploy **only** `deployFiles` / generated `.svc`, `.api`, `.apy` — **never** raw `.plsvc` to SQLcl.

```powershell
node .claude/skills/ifs-codegen/tools/ifs-deploy.mjs "ifsapp/ifsapp@<dbHost>:1521/IFSPDB" <file1> <file2>
```

`dbHost` from `docs/bnd-environment-connections.json`. Keep a `deploy-*.ps1` next to the suite.

---

## 7. Run and self-correct

Default exe: `c:\Users\gunslk\Downloads\publish-commandline\ScriptARest.exe` if present; else `sarRunner.executablePath` from Cursor settings. ServerUrl from bnd env (DEV CMB: `https://ifsmasterbnddevcmb.rnd.ifsdevworld.com`).

```powershell
& $exe "ServerUrl=$server" "FileToRead=<absolute-mkd>" 2>&1
```

Credentials: appsettings / Connect in `.mkd`. Do not print passwords.

Order:

1. One core case (setup + asserts).
2. Remaining core cases (prefer individually if InventoryPartSet 500 on bulk recreate).
3. `RunCoreMatrix.mkd`.

A case is green when Test Report `Passed` and Failed asserts / Exceptions for **that** case are 0 (CatchError siblings may still error in a suite run).

### Classifier (fix without asking)

| Class | Action |
| --- | --- |
| Syntax (expecting `{`) | Edit Call |
| Unknown identifier | Output keys; refetch |
| UNKNOWN_CONTENT | Codegen+deploy |
| string has no Objstate | Refetch by key |
| BPA OperationNo / 504 / InventoryPartSet 500 | Retry util / individual runs; do not drop asserts |
| No such host | RESULTS; stop |

Max **8** ScriptARest attempts per case. After each `.mkd` edit, re-read the file before the next run.

---

## 8. RESULTS.md

Record:

- Environment, date, deploy note, log path under `.sar-fda/`
- Core case table: CO/ChangeId if known, pass/fail
- **Newly automated** vs **skipped as inttst duplicates** vs **manual/variant**
- Env blockers (VPN, deploy missing)

---

## 9. Success

Core **gap** cases Passed, or an explicit env blocker. Do not claim green if only syntax-parse ran with 0 server calls.
