---
name: ifs-master-commit
description: >-
  Create a 27R1 bugfix branch from origin/master and commit only the files that
  fix a given Jira key. Resolves checkout/overlay conflicts, runs a GPT 5.6
  A–Z IFS code/fix review before commit, then pushes (no Bitbucket PR, no Jira
  writes). Use when the user asks to commit the master fix, create the 27R1
  branch, run /commit-master-fix, or start the master-fix-commit agent. Run
  this workflow as Composer 2.5. Do not use for support-track backports.
---

# IFS Master Fix Commit

Commit an **already-written** master-track defect fix. Cut `bugfix/gunslk/27R1-<JIRA>-<slug>` from latest `origin/master`, commit **only** that ticket’s files, push. The user opens the Bitbucket PR.

Branch, commit subject, history sign, and “never put `master` in the branch name” come from [`ifs-track-backport/references/formats-and-mapping.md`](../ifs-track-backport/references/formats-and-mapping.md). **Current master track is `27R1`.** Master commit has **no** `- 27R1` suffix.

**Run as Composer 2.5.** Parent / `/commit-master-fix` must launch this agent with model Composer 2.5. Do not invent the functional fix. When launched from **ifs-mfg-defect-analysis** Step 9, the parent already obtained user **yes**. Standalone `/commit-master-fix` is itself confirmation.

## Hard stops

- **No Bitbucket PRs** — do not call `create_pull_request`, `backport_fix`, or POST `/pullrequests`.
- **No Jira writes** — read only.
- **No bug tags** — history comment only.
- **No `git add .` / `git add -A`** — stage the ticket-file list only.
- **No full-tree `git stash`.** Snapshot ticket files by copying those paths aside.
- **Never commit on `master`.** `git branch --show-current` must be the new bugfix branch first.
- **Never commit files that are not this issue’s fix.**
- **No `Co-authored-by: Cursor`**, any `Co-authored-by`, `--trailer`, second `-m`, or commit body. One `-m` line only.
- **No force-push.**
- Do not leave `<<<<<<<` / `=======` / `>>>>>>>` in committed files. **Resolve** checkout/overlay conflicts; do not stop with them unsolved.
- Do not commit if GPT 5.6 review is **blocking** (wrong/incomplete fix, or unfixed mandatory IFS checklist failures).
- Do not invent a fix or revert unrelated local edits.

Ignore `ifs-bitbucket-merge` comma commit style (`MFZ-30494, Fixed ...`).

## Mandatory companion skills

1. `ifs-track-backport` reference `formats-and-mapping.md` — branch + master commit line
2. `ifs-jira-reader` — ticket summary
3. `ifs-history-comments` — placement; **sign `GUNSLK`**, date = **today**
4. `ifs-code-review` — GPT 5.6 A–Z review uses this checklist

## Inputs

| Input | Required |
|-------|----------|
| Jira key | Yes |
| Explicit file list | No — derive from dirty files + ticket rules |

Git root: `c:\Dev\Master\workspace`.

## Ticket-file selection

When launched from **ifs-mfg-defect-analysis** Step 9, the file list is the applied DUT source in `docs/<JIRA>/analysis.md` Step 5 — not every dirty path.

Build an explicit path list **before** `git add`. Include a dirty/untracked file only if it is part of **this** issue’s fix:

- Parent handed the DUT paths from analysis.md, **or**
- Path or `git diff` content mentions the Jira key, **or**
- History line already has `GUNSLK  <JIRA>` / the ticket id, **or**
- The user named the files.

**Exclude** by default: `.sar-fda/**`, other Jira keys, generated noise, unrelated skills/agents, docs not named by the user.

If more than one plausible set exists, list candidates (ticket vs leftover) and **ask**. Do not guess a mixed commit.

## Checkout conflicts (resolve, do not abort)

1. Copy ticket-file contents aside (not a full-tree stash).
2. `git fetch origin master`.
3. `git checkout -b bugfix/gunslk/27R1-<JIRA>-<slug> origin/master` (or checkout that branch if it already exists).
4. Overlay the snapshot onto the ticket paths.
5. If Git refuses overwrite or files contain conflict markers:
   - **Code hunks for this defect:** keep the local fix.
   - **Unrelated hunks:** take `origin/master`.
   - **History blocks:** keep existing lines; insert today’s `GUNSLK  <JIRA>,` line at the top. Do not drop the functional fix.
6. Continue until no `unmerged` paths. Ticket files contain the fix. Leftover dirty files stay unstaged — do not `git add` them to clear a conflict.

## Workflow

```powershell
# identify ticket files; do not git add . ; do not commit on master
git fetch origin master
git checkout -b bugfix/gunslk/27R1-<JIRA>-<slug> origin/master
# overlay snapshot; resolve markers (keep this fix)
git branch --show-current   # must be the new branch, not master
git add <ticketFile1> <ticketFile2>
git commit -m "<JIRA>: <Jira summary>"   # one line; no Co-authored-by; no body
git push -u origin bugfix/gunslk/27R1-<JIRA>-<slug>
```

1. If the Jira key is missing, ask. `git status` at the git root. If no ticket files, stop. If current branch is not `master` and not the intended `bugfix/gunslk/27R1-...` branch, stop and ask.
2. Read Jira (`getJiraIssue`, `cloudId: "ifsdev.atlassian.net"`, markdown). Commit subject = `<JIRA>: <Jira summary>` (exact summary).
3. Slug: ~5–6 lowercase kebab words from the summary; include the CS number when present. Never put `master` in the branch name.
4. History on **ticket files** that have a header: newest first after the separator, match that file’s spacing, `GUNSLK`, today `YYMMDD`. No `--<JIRA>, Start/End`. Skip `.entity`.
5. Snapshot → fetch → create branch from `origin/master` → overlay → **resolve conflicts**.
6. Confirm `git branch --show-current` is the new branch. If still `master`, stop.
7. **GPT 5.6 A–Z review (before commit).** Launch one Task with model **GPT 5.6** (`gpt-5.6-sol-medium`), not Composer, not Bugbot. Prompt must include: Jira key and summary, ticket file paths, `git diff` of those files vs `origin/master`, and: follow `.claude/skills/ifs-code-review/SKILL.md` end-to-end for every applicable file type; judge whether the change actually fixes the ticket and what it might break. Return pass / blocking / nits with file:line. Then: apply straightforward blocking IFS/checklist fixes on **ticket files only**. **Stop and show the user** if the review says the defect is not actually fixed. Do not commit on a blocking fail. Nits go in wrap-up.
8. `git add` only the ticket-file list. Leftovers stay unstaged. `git diff --cached --name-only` must equal that list. Confirm `GUNSLK` + today’s date on staged files that have a history header.
9. `git commit -m "<JIRA>: <Jira summary>"` only. After commit, `git log -1 --format=%B` must be that single subject (optional trailing newline). If a trailer appeared, do not push; fix the message without adding Cursor co-author (prefer a new commit only if the first commit has not been pushed and the user did not forbid amend — **do not amend** unless the first commit was yours in this session, succeeded, and is unpushed; otherwise stop and report).
10. `git push -u origin <branch>`.
11. Wrap-up table:

| Track | Branch | Destination | Suggested PR title | Remote | GPT 5.6 review |
|-------|--------|-------------|--------------------|--------|----------------|
| 27R1 | `bugfix/gunslk/27R1-...` | `master` | same as commit | `https://bitbucket.org/ifs-pd/ifs-applications/branch/<branch>` | pass / blocking-fixed / nits |

Mention leftover unstaged files so they are not lost.

Optional reviewers (user creates the PR): Jimmy Cederholm, Kalana Chandrasekara, Yashora Jayamanne, Hansa Gunasinghe.
