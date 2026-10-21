# Track backport — formats and mapping

Source of truth: MFZ-30494 sample PRs (master 229989, then 231801 / 231796 / 231715 / 231707).

## User and git

| Item | Value |
|------|--------|
| Branch user id | `gunslk` |
| History sign | `GUNSLK` (not `slpelk`) |
| Git root | `c:\Dev\Master\workspace` |
| Worktrees | `c:\Dev\Master\worktrees\<TRACK>-<JIRA>` |
| Remote repo | `ifs-pd/ifs-applications` |
| Bug tags | **Do not add** (match samples) |

## Track → base branch → SQLcl → JDBC

| Track | Base branch (cut from / PR destination) | SQLcl connection | JDBC (`ifsapp/ifsapp@HOST:1521/IFSPDB`) |
|-------|------------------------------------------|------------------|----------------------------------------|
| `27R1` (master) | `master` | `MASTER DEV CMB` — **skip**; already done | — |
| `26R2` | `release/26.2` | `26R2 DEV CMB` | `AZSG1PDE596` |
| `26R1` | `release/26.1` | `26R1 DEV CMB` | `AZSG1PDE573` |
| `25R2` | `release/25.2` | `25R2 DEV CMB` | `AZSG1PDE539` |
| `25R1` | `release/25.1` | `25R1 DEV CMB` | `AZSG1PDE109` |
| `24R2` | `release/24.2` | `24R2 DEV CMB` | `DLK1PDE485` |
| `24R1` | `release/24.1` | Ask user (no default DEV CMB) | Ask user |

Never put the word `master` in a branch name. Master currently maps to **27R1**. Existing MASTER CMB environments are the 27R1 databases.

Process support tracks **newest to oldest**: 26R2 → 26R1 → 25R2 → 25R1 → 24R2.

Worktrees: `c:\Dev\Master\worktrees\<TRACK>-<JIRA>`. **Always recreate** (remove `-f -f` then `worktree add`). Checkout takes **3–5 minutes** — use a **300s+** timeout.

## Branch name

```
bugfix/gunslk/<TRACK>-<JIRA>-<short-kebab>
```

- Reuse the **same kebab slug** on every track; only `<TRACK>` changes.
- Slug from the Jira summary, ~5–6 words, include the CS number when present.
- Lowercase kebab-case.

Samples:

```
bugfix/gunslk/27R1-MFZ-30494-cs0545623-allocate-only-breaks
bugfix/gunslk/26R2-MFZ-30494-cs0545623-allocate-only-breaks
bugfix/gunslk/26R1-MFZ-30494-cs0545623-allocate-only-breaks
bugfix/gunslk/25R2-MFZ-30494-cs0545623-allocate-only-breaks
bugfix/gunslk/25R1-MFZ-30494-cs0545623-allocate-only-breaks
bugfix/gunslk/24R2-MFZ-30494-cs0545623-allocate-only-breaks
```

Older tickets may still have master branches named `bugfix/gunslk/26R2-<JIRA>-<slug>` from when master was 26R2. Reuse that kebab slug; only change `<TRACK>`.

## Commit message (and suggested PR title)

**Same one-line string.** No commit body. Do **not** use `ifs-bitbucket-merge` comma style (`MFZ-30494, Fixed ...`). Do **not** add `Co-authored-by: Cursor`, any `Co-authored-by`, `--trailer`, or a second `-m` body.

```
<JIRA>: <Jira summary>              # master only
<JIRA>: <Jira summary> - <TRACK>    # every support track
```

`<TRACK>` is the **destination** track (`25R1` when targeting `release/25.1`). Do not copy a typo from another track.

Real sample subjects:

```
MFZ-30494: CS0545623 Allocate Only breaks the connection on order numbers
MFZ-30494: CS0545623 Allocate Only breaks the connection on order numbers - 26R2
MFZ-30494: CS0545623 Allocate Only breaks the connection on order numbers - 26R1
MFZ-30494: CS0545623 Allocate Only breaks the connection on order numbers - 25R2
MFZ-30494: CS0545623 Allocate Only breaks the connection on order numbers - 25R1
MFZ-30494: CS0545623 Allocate Only breaks the connection on order numbers - 24R2
```

(The 25R1 sample PR/commit incorrectly used `- 25R2`. Use `- 25R1`.)

```
git commit -m "<JIRA>: <Jira summary> - <TRACK>"
```

Bitbucket merge messages (`Merged in bugfix/... (pull request #N)`) are created on merge. Do not write those.

## History comment

Placement: newest first, immediately after the `--  ------  ------  ---...` separator. Match that file’s spacing. Follow `ifs-history-comments` except **sign is `GUNSLK`** and **date is today (`YYMMDD` of the port day)** — **never copy master’s `YYMMDD`**.

Copy the description text from the master history line (the part after `<JIRA>,`).

Put the correct date on the **first** commit for that track. Scan changed files after cherry-pick and replace any copied master date **before** `git add` / `git commit`. Do not commit then amend.

Sample (24R2 port on 260825; master had 260811):

```
--  260825  GUNSLK  MFZ-30494, Modified Release_To_So___ to seed shop order keys from customer order when creating SO from CTP interim.
```

No `--<JIRA>, Start` / `--<JIRA>, End` wrappers.

## Cherry-pick conflicts

Cherry-pick the master developer commit. Typical conflicts are **history blocks** (PCA / ConfigMediaManager style). Resolve like this:

**History hunk**

```
<<<<<<< HEAD
--  <track’s newest existing lines>
=======
--  <master date>  GUNSLK  <JIRA>, <description>
--  <master-only later history — do not copy onto this track>
>>>>>>> <commit>
--  <shared older history>
```

Keep HEAD’s existing lines. Insert one new line at the top with **today’s** date:

```
--  <TODAY YYMMDD>  GUNSLK  <JIRA>, <description>
--  <track’s newest existing lines>
--  <shared older history>
```

Do **not** add incoming history that only exists on master or newer tracks (e.g. a `SMDEV-` / later `MFDEV-` line the older track never had).

**Code hunk**

Take the incoming functional change (new method, call-site swap). If HEAD is empty and incoming is the new method, take incoming. If signatures differ, stop and show master vs target.

## Deploy playbook

Use **`py`**, not `python`, for codegen:

```
py .claude/skills/ifs-codegen/tools/ifs-codegen.py generate <worktree-model> --json
node .claude/skills/ifs-codegen/tools/ifs-deploy.mjs "ifsapp/ifsapp@<HOST>:1521/IFSPDB" --script <masterScript>
```

Rules:

- Generate from the **worktree** model (`.utility`, `.entity`, `.projection`).
- Do **not** deploy raw `.plsql` that still has `layer Core` via `ifs-deploy.mjs`.
- `.utility` (no `.entity`): generate from `.utility`, deploy `.api` + `.apy` via the master script — not `fast-deploy-plsql.ps1`.
- Order: utility/entity first, then projections. If `PartConfigurationAssistantHandling.projection` (or similar) errors on a `*_TST` test package at EOF, the main SVC body may still be VALID — check SQL, then deploy remaining projections separately (e.g. `B2bConfigurationService.projection`).
- Entity deploy can fail (missing table, `Security_SYS.Check_Data_Access_*`). Judge by **changed package bodies VALID** and `user_source` containing the fix method — not by script exit 0.

**Per-ticket helper:** when the same generate+deploy sequence repeats across tracks, add `scripts/deploy-<jira-lower>-track.ps1` (example `scripts/deploy-mfz30520-track.ps1`: Worktree + JdbcConn, `Deploy-FromModel` each model). If a step throws, continue remaining models one by one and verify VALID in SQL.

**Invalid-object check** (list the packages this ticket actually changed):

```sql
SELECT object_name, object_type, status
FROM user_objects
WHERE object_name IN ('CONFIG_MEDIA_MANAGER_API', 'ORDER_CONFIGURATION_TMP_API', ...)
  AND object_type IN ('PACKAGE', 'PACKAGE BODY')
ORDER BY object_name, object_type;
```

**24R2 DEV CMB (`DLK1PDE485`):** generated CRUD may reference `Security_SYS.Check_Data_Access_For_Create/Update/Delete` or `CHECK_ACCESS_PROJECTION_ACTION` that are not on that CMB. Compile INVALID for that reason is **environment drift**, not a bad port. Report it. Do not treat it as a failed defect deploy. Avoid a full entity master-script redeploy if that is what invalidated previously VALID packages. Still push the source branch.

## Suggested PR wrap-up (user creates the PR)

Print after all tracks. Do not call Bitbucket create-PR APIs.

| Column | Value |
|--------|--------|
| Track | e.g. `25R2` |
| Branch | `bugfix/gunslk/...` |
| Destination | e.g. `release/25.2` |
| Suggested title | same as commit message |
| Remote | `https://bitbucket.org/ifs-pd/ifs-applications/branch/<branch>` |
| Deploy notes | VALID / env-only INVALID (e.g. 24R2 Security_SYS) |
| Recreate SAR | Master MKD or `docs/<JIRA>/recreate/<TRACK>/` + pass/fail |

## Recreate SAR on a support track

After 3c, before commit. `FileToRead` the master workspace MKD: `c:\Dev\Master\workspace\docs\<JIRA>\recreate\Recreate*.mkd`. `Username`/`Password` `alain`. `ServerUrl` = that track’s DEV CMB **origin** (no `/main/ifsapplications/web/`):

| Track | ScriptARest ServerUrl |
|-------|------------------------|
| 26R2 | `https://ifs26r2bnddevcmb.rnd.ifsdevworld.com` |
| 26R1 | `https://ifs26r1bnddevcmb.rnd.ifsdevworld.com` |
| 25R2 | `https://ifs25r2bnddevcmb.rnd.ifsdevworld.com` |
| 25R1 | `https://ifs25r1bnddevcmb.rnd.ifsdevworld.com` |
| 24R2 | `https://ifs24r2bnddevcmb.rnd.ifsdevworld.com` |

Confirm hosts in `docs/bnd-environment-urls.md`. If the master recreate script needs track-only edits, copy to `docs/<JIRA>/recreate/<TRACK>/` and add one `../` on relative `Call`s. Do not change the master file.

Optional reviewer reminder: Jimmy Cederholm, Kalana Chandrasekara, Yashora Jayamanne, Hansa Gunasinghe.

## Finding the master fix

1. Optional user-supplied master PR URL.
2. Else Bitbucket search: title contains `<JIRA>`, destination `master` (OPEN or MERGED).
3. Else `git log --all --grep="<JIRA>"` on `bugfix/gunslk/27R1-<JIRA>-*`, `bugfix/gunslk/26R2-<JIRA>-*` (older master-era names), or `master`.

Read the **developer** commit on the bugfix branch (subject = title format), not the merge commit.
