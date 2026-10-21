---
name: ifs-jira-rca
description: Record Root Cause Analysis on IFS Jira Defect tickets — theme, sub-theme, root cause narrative, preventive actions, and Introduced In. Use when performing RCA, updating the Root Cause Analysis tab, or after a defect fix is complete. Triggers on RCA, root cause analysis, preventive action, Introduced In, Root Cause Theme.
---

# IFS Jira Root Cause Analysis

Workflow for drafting and (with user approval) updating RCA fields on IFS Defect issues.

## Jira Configuration

- **Site**: `ifsdev.atlassian.net`
- **cloudId**: `ifsdev.atlassian.net`
- Read tickets per **ifs-jira-reader** skill (issue, comments, linked issues, attachments).

## Required User Input

| Input | Required | Description |
|---|---|---|
| **Jira ID** | Yes | e.g. `MFZ-29917`, `HRZ-20473` |
| **Fix** | Yes | What was changed to resolve the defect — files, logic, tests added |

Optional: Introduced In timeframe, git blame/commit, extra investigation notes.

## Draft-First Rule (Mandatory)

**Never update Jira until the user explicitly approves the draft.**

1. Produce the RCA draft (see output template below).
2. Present it to the user.
3. Ask: *"Would you like me to update Jira ticket \<KEY\> with this RCA? Reply **yes**, **no**, or **edit** with changes."*
4. Only on **yes** (or after incorporating **edit** feedback and re-confirming) → update Jira.

## Analysis Workflow

### Step 1 — Gather context

1. Fetch issue: `getJiraIssue` with `cloudId: "ifsdev.atlassian.net"`, `responseContentFormat: "markdown"`.
2. Read summary, description, components, reported version, comments (chronological).
3. Fetch linked issues (swarming, duplicates, parent) for prior RCA notes.
4. Incorporate the user's **fix** description and any code/investigation context available in the conversation.

### Step 2 — Answer the three RCA questions

1. What is the **underlying problem** (not just the symptom)?
2. Why **couldn't we detect** this before release?
3. How can we **prevent** similar issues?

### Step 3 — Classify theme and sub-theme

Use the taxonomy in [references/rca-themes-and-guidelines.md](references/rca-themes-and-guidelines.md). Pick the **best-fit** main theme and sub-theme from the table.

### Step 4 — Draft preventive action(s)

- **Process** or **Tools** theme → preventive action is **required**.
- **Reasonable Defect** → recommend if applicable; not mandatory.
- State whether each action is **done with the fix** or **planned separately** (linked Preventive Action issue).

### Step 5 — Recommend Introduced In (when possible)

Use git history (`git blame`, `git log`) if available. Otherwise infer from investigation or suggest `Unknown` with brief rationale.

Half-year format: `YY-H1` (Jan–Jun) or `YY-H2` (Jul–Dec) for the year the bug was **introduced**.

### Step 6 — Present draft and wait

Use the output template. **Stop.** Do not call `editJiraIssue` yet.

## Output Template (Show User First)

```markdown
## RCA Draft — {JIRA-KEY}: {summary}

| Field | Value |
|---|---|
| **Root Cause Theme** | {Process \| Tools \| Reasonable Defect} |
| **Root Cause Sub-theme** | {sub-theme from taxonomy} |
| **Introduced In** | {half-year \| Pre-Existing \| Unknown} |

### Brief Root Cause
{2–5 sentences: underlying problem, why not detected, technical explanation tied to the fix}

### Preventive Action(s)
{Numbered list. For each: action, owner/area if cross-team, done-with-fix vs separate Jira issue}

---
**Approve Jira update?** Reply **yes** / **no** / **edit** (with changes).
```

Keep **Brief Root Cause** concise — it goes into the Jira **Root Cause** field. Expand only if the user asks.

## Updating Jira (After Approval Only)

### Step A — Resolve field IDs

```
getJiraIssueTypeMetaWithFields
  cloudId: "ifsdev.atlassian.net"
  projectIdOrKey: "<project from issue key>"
  issueTypeId: "<Defect issue type id from getJiraIssue>"
```

Map: Root Cause Theme, Root Cause, Preventive Action, Introduced In.

If field IDs are unclear, fetch the issue with `fields: ["*all"]` and inspect existing custom field names.

### Step B — Update fields

```
editJiraIssue
  cloudId: "ifsdev.atlassian.net"
  issueIdOrKey: "<JIRA-KEY>"
  fields: { ... }
  contentFormat: "markdown"
```

Set:
- **Root Cause Theme** — value matching Jira allowed options (theme + sub-theme as configured).
- **Root Cause** — brief root cause text from draft.
- **Preventive Action** — preventive action text (when applicable).
- **Introduced In** — dropdown value when determined.

### Step C — Confirm to user

After update, fetch the issue again and show the fields that were written. If any field failed (wrong option, permission), report the error and show what was attempted.

## Separate Preventive Action Issue

If the user wants a **separate** Preventive Action work item (not only the field):

1. Tell the user it is typically created via workflow transition (*Create Preventive Action* checkbox) or manual **Create** with link to the Defect.
2. Offer to draft the **Preventive Action Summary** title and description for them to paste — do **not** create Jira issues unless the user explicitly asks after approving.

## Additional Resources

- [RCA themes & guidelines](references/rca-themes-and-guidelines.md) — full taxonomy and Introduced In rules
- [ifs-jira-reader](../ifs-jira-reader/SKILL.md) — reading Jira tickets
- `ifs-git-history` (not bundled in this plugin) — tracing when a defect was introduced; see `.claude/skills/ifs-git-history/SKILL.md` in your workspace if available
