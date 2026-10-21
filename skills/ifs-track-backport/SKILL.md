---
name: ifs-track-backport
description: >-
  Ports an already-verified IFS Cloud master-track defect fix to previous
  release tracks (26R2, 26R1, 25R2, 25R1, 24R2): create bugfix branches, apply the
  same change with track history comments, deploy to that track's DEV CMB,
  confirm changed packages compile, run the ticket Verify SAR (fix asserts),
  commit and push. Does not create Bitbucket PRs. If the Verify SAR needs
  track-specific edits, copy it — do not change the master Recreate or Verify file.
  Browser/Aurena testing only if the user asks. Use when the user asks to
  apply the fix to previous tracks, backport, port to planned versions, run
  /apply-previous-tracks, or start the track-backport agent after the master
  fix is verified.
---

# IFS Track Backport

Port a **verified master fix** to every other IFS Planned Version track. Commit and push each branch. The user opens Bitbucket PRs.

To **create the master (27R1) branch and commit** the original fix, use **ifs-master-commit** / the **master-fix-commit** agent (`/commit-master-fix`), not this skill.

Read [formats-and-mapping.md](references/formats-and-mapping.md) before branching.

## Hard stops

- **No Bitbucket PRs** — do not call `create_pull_request`, `backport_fix`, or POST `/pullrequests`.
- **No Jira writes** — read only (workspace rule).
- **No bug tags** — history comment only, matching the sample PRs.
- **No `git add .` / `git add -A`** — stage explicit paths.
- **No stash.** Stop if **tracked product source** outside this ticket’s DUT list is dirty. Untracked `docs/<JIRA>/`, skills, and `.sar-fda` do **not** block. Do not `git add .`.
- **No commit** until deploy has been attempted, changed packages are checked (3c), **and Verify SAR fix asserts pass** (3d). Do not commit with master’s history date.
- **No guessing** if the target-track code does not match — stop and show an adapted patch.
- **No Aurena / browser test** unless the user explicitly asks.

Do not use codegen MCP `backport_fix` as the engine.

## Mandatory companion skills

Read and follow as needed:

- `ifs-jira-reader` — ticket, summary, IFS Planned Versions
- `ifs-bitbucket-merge` — track ↔ base branch (override commit/PR title format with this skill)
- `ifs-history-comments` — placement/spacing; **sign `GUNSLK`**, date = **today** (port day, not master’s)
- `ifs-codegen` — generate/deploy before commit
- Verify SAR: `docs/<JIRA>/recreate/Verify*.mkd` and `ifs-mfg-defect-analysis` [recreate-sar.md](../ifs-mfg-defect-analysis/references/recreate-sar.md) for ServerUrl origin / `alain` / fix asserts

Read `ifs-aurena-navigate` and `ifs-browser-test` **only** when the user asks for browser testing.

## Inputs

| Input | Required |
|-------|----------|
| Jira key (e.g. `MFZ-30494`) | Yes |
| Master PR URL | No — search if omitted |

Prerequisite: master fix is already applied and verified. Do not invent a new fix. When launched from **ifs-mfg-defect-analysis** Step 10, the parent already obtained user **yes**. Standalone `/apply-previous-tracks` is itself confirmation.

## Workflow

### 1. Read Jira

`getJiraIssue` with `cloudId: "ifsdev.atlassian.net"`, markdown. Extract summary and **IFS Planned Versions** (custom field and/or comments like `24.2.22 - 24R2 SU22`). Map version prefixes per `ifs-jira-reader`.

Skip `27R1` / master. Remaining tracks, newest first: **26R2 → 26R1 → 25R2 → 25R1 → 24R2** (omit any not in Planned Versions).

### 2. Capture the master fix

Find the master PR/commit (see reference). Record:

- Changed file paths
- Semantic diff (methods, added/removed lines)
- Master history-comment **description** (text after `<JIRA>,`)
- Master history **date** (so you can recognize and replace it — do not copy it)
- Kebab slug from the master branch name if it matches `bugfix/gunslk/27R1-<JIRA>-<slug>` (or an older master-era `bugfix/gunslk/26R2-<JIRA>-<slug>`); otherwise build from the summary

### 3. Per-track loop

Git root: `c:\Dev\Master\workspace`.

```powershell
git -C "c:\Dev\Master\workspace" status
```

If **tracked product source** outside this ticket’s DUT list is dirty, **stop**. Untracked `docs/<JIRA>/`, skills, and `.sar-fda` are not a stop.

For each target track:

#### 3a. Worktree + branch (always recreate)

Checkout of a full worktree takes **3–5 minutes**. Use a **300s+** command timeout.

If `c:\Dev\Master\worktrees\<TRACK>-<JIRA>` already exists, **remove it and recreate** — do not reuse:

```powershell
git -C "c:\Dev\Master\workspace" worktree remove -f -f "c:\Dev\Master\worktrees\<TRACK>-<JIRA>"
```

Then:

```powershell
git -C "c:\Dev\Master\workspace" fetch origin <base-branch>
git -C "c:\Dev\Master\workspace" worktree add "c:\Dev\Master\worktrees\<TRACK>-<JIRA>" origin/<base-branch>
cd "c:\Dev\Master\worktrees\<TRACK>-<JIRA>"
git checkout -b bugfix/gunslk/<TRACK>-<JIRA>-<slug>
```

If `worktree remove` fails because of a lock, retry `-f -f`. Do not leave a half-created worktree and continue.

#### 3b. Apply the equivalent fix

Cherry-pick the **master developer commit** (not the merge commit). Then resolve conflicts by hand — especially history blocks.

```powershell
git cherry-pick <master-commit>
```

1. Keep the **track’s** existing history lines. Insert the new `GUNSLK` line at the top with **today’s `YYMMDD`**.
2. Do **not** add incoming history lines that exist only on master / newer tracks.
3. Take incoming **code** hunks for the defect. If methods or signatures differ: **stop**, show master vs target, propose an adapted patch, wait.
4. Port tests only if they were part of the master fix.

**History date on the first commit — no amend later.** After cherry-pick (and any conflict resolution), **before** `git add` / `git commit`:

- Scan every changed file for `GUNSLK  <JIRA>`.
- Every such line must use **today’s** `YYMMDD`. Replace any copied master date (e.g. `260820`) now.
- Match that file’s spacing. Description text = the part after `<JIRA>,` from master.

Do not commit, then notice the date, then amend. Get it right before the first `git commit` on that track.

Conflict templates and deploy notes: [formats-and-mapping.md](references/formats-and-mapping.md).

#### 3c. Deploy (before commit)

Use `ifs-codegen` against **worktree** paths, not `c:\Dev\Master\workspace\...`. Connection = `<TRACK> DEV CMB` (JDBC hosts in the reference).

When the same multi-file generate+deploy sequence will run on every track, create or reuse `scripts/deploy-<jira-lower>-track.ps1` (example: `scripts/deploy-mfz30520-track.ps1`). Use **`py`**, not `python`.

Playbook (see reference for details):

1. Generate from the model (`.utility` / `.entity` / `.projection`) in the worktree, then deploy the **master script**.
2. Do **not** deploy raw `.plsql` that still has `layer Core` via `ifs-deploy.mjs`.
3. Order: utility/entity first, then projections. If a projection fails on a test package at EOF, check whether the main SVC body is still VALID, then deploy remaining projections separately.
4. Entity/script exit code 0 is not enough — query the changed packages.

Then run the **concrete** invalid-object check for the packages this ticket changed (names from the master fix, `_API` / `_SVC` as applicable):

```sql
SELECT object_name, object_type, status
FROM user_objects
WHERE object_name IN ('<PKG1_API>', '<PKG2_SVC>', ...)
  AND object_type IN ('PACKAGE', 'PACKAGE BODY')
ORDER BY object_name, object_type;
```

Also confirm the fix text is in the DB (method name from the master diff):

```sql
SELECT name, COUNT(*) AS refs
FROM user_source
WHERE UPPER(text) LIKE '%<KEY_METHOD>%'
  AND name IN ('<PKG1_API>', '<PKG2_SVC>', ...)
GROUP BY name
ORDER BY name;
```

**24R2 / older DEV CMB:** generated CRUD may call `Security_SYS.Check_Data_Access_*` (or `CHECK_ACCESS_PROJECTION_ACTION`) that the CMB does not have. That is environment drift, not a failed port. Do not leave the ticket source unpushed for that reason. Report it in the wrap-up. Avoid redeploying full generated entity CRUD if that is what invalidated previously VALID packages.

If invalids are from **this** defect’s logic (missing method, compile error in the changed code): do not commit; fix or wait.

#### 3d. Verify (before commit)

**SQL:** 3c VALID + fix-text checks must already have passed.

**Verify SAR (mandatory):** confirm the **fix** on this track’s DEV CMB before commit.

1. Find the master **Verify** MKD (`docs/<JIRA>/recreate/Verify*.mkd`) in **`c:\Dev\Master\workspace`** (not the worktree). `FileToRead` that path so `Call ../../../inttst/...` still resolves. If none exists, **stop and ask**. Do not run the Recreate (bug-assert) MKD as the pass gate.
2. Run ScriptARest: `Connect alain` / username `alain` / password `alain`. `ServerUrl` is the **origin only** for **this track’s DEV CMB** from `docs/bnd-environment-urls.md` (strip `/main/ifsapplications/web/`). Examples: 26R2 `https://ifs26r2bnddevcmb.rnd.ifsdevworld.com`, 26R1 `https://ifs26r1bnddevcmb.rnd.ifsdevworld.com`.
3. Require **fix asserts**. Do not require Recreate bug asserts to pass on the patched track.
4. **Track-specific copy:** if the run fails because of a **track difference** (util path, projection, basic data, payload — not a missing product fix), **do not edit** the master Recreate or Verify MKD. Copy Verify (and local `util/` if used) to `docs/<JIRA>/recreate/<TRACK>/`. Fix **only that copy** (add one `../` on relative `Call` paths into `inttst` and local `util/`). Re-run until fix asserts pass. Other tracks still start from the master Verify file unless they need their own copy.
5. If fix asserts fail because the **product port is wrong**: do not commit; do not weaken asserts. Investigate the port.
6. Record in the wrap-up: Verify SAR path used (master vs `recreate/<TRACK>/`) and pass/fail.

**Browser / Aurena:** only when the user explicitly asks. Then use `ifs-aurena-navigate` + `ifs-browser-test` on that track’s env. If the URL is unknown, ask once.

#### 3e. Commit and push (no PR)

Confirm history dates one last time on the staged files, then:

```powershell
git add <file1> <file2>
git status
git commit -m "<JIRA>: <Jira summary> - <TRACK>"
git push -u origin bugfix/gunslk/<TRACK>-<JIRA>-<slug>
```

One-line message, colon format, destination track suffix. No commit body.

### 4. Wrap-up (user creates PRs)

Print a table: Track | Branch | Destination | Suggested PR title | Push URL | Deploy notes (VALID / env-only INVALID) | Verify SAR (path + pass/fail).

Suggested title = commit message. Optional reviewer reminder from the reference.

## Quality checks

- Branch slug identical across tracks except `<TRACK>`
- History date on the **first** commit is the port date, not master’s
- Support-track title suffix matches destination (`- 25R1` for `release/25.1`)
- Only ticket files in the commit (track SAR copies live under `docs/<JIRA>/recreate/<TRACK>/` in the master workspace — they are **not** part of the track source commit unless the user asks)
- Verify SAR fix asserts passed on that track DEV CMB (or stopped and asked)
- No Aurena run unless the user asked
