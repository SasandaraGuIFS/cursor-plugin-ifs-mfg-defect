---
name: ifs-jira-release-notes
description: Draft and update the mandatory Release Notes field on IFS Jira Defect issues when closing tickets. Use when writing release notes, Service Update report text, Patch Report content, closing a defect, or when the user mentions Release Notes, SU Report, ExcludeFromSUReport, bug correction impact, or CVE/CVSS for a fix.
---

# IFS Jira Release Notes

Workflow for drafting customer-facing **Release Notes** on IFS Defect issues before closing. Content is extracted into the Service Update Fixes Report and, from UPD25 onward, the APP10 Patch Report.

## Jira Configuration

- **Site**: `ifsdev.atlassian.net`
- **cloudId**: `ifsdev.atlassian.net`
- Read issue context per **ifs-jira-reader** skill.

## Required User Input

| Input | Required | Description |
|---|---|---|
| **Jira ID** | Yes | e.g. `MFZ-29885`, `HRZ-20473` |
| **Fix** | Yes | What was changed — files, logic, data, performance, tests |

Optional: manual steps for customers, data table changes, security/CVE details, whether to exclude from SU/Patch report.

## Draft-First Rule (Mandatory)

**Never update Jira until the user explicitly approves the draft.**

1. Produce the release note draft (see output template below).
2. Present it to the user.
3. Ask: *"Would you like me to update the Release Notes field on Jira ticket \<KEY\> with this text? Reply **yes**, **no**, or **edit** with changes."*
4. Only on **yes** (or after incorporating **edit** feedback and re-confirming) → update Jira.

If certain fix information must be excluded from the Service Update or New Patch Report, recommend adding **ExcludeFromSUReport** in the **Tags** field (not Labels). Explain why and ask whether to apply that tag when updating Jira.

## Analysis Workflow

### Step 1 — Gather context

1. Fetch issue: `getJiraIssue` with `cloudId: "ifsdev.atlassian.net"`, `responseContentFormat: "markdown"`.
2. Read summary, description, components, fix version, and comments for customer-visible behavior — use this only to understand the fix, **not** to restate the defect in the release note.
3. Incorporate the user's **fix** description and any code changes, deployment notes, or verification results from the conversation.

### Step 2 — Identify what belongs in the release note

Write from the **customer's point of view**. Include only what helps them understand what was corrected and what they may need to do.

| Topic | Include when |
|---|---|
| **Solution** | Always — high-level description of what was done |
| **Bug correction impact** | Fix changes behavior, data, integrations, or requires customer awareness |
| **Manual steps / interventions** | Customer or consultant action needed after applying the fix |
| **Performance enhancement** | Fix included measurable or user-visible performance improvement |
| **Data table changes** | Schema, migration, or data correction touches tables |
| **Security (CVE/CVSS)** | Security-related fix — only approved security information |

Do **not** include: detailed issue description, internal investigation, ticket links, customer or person names, track-merge boilerplate.

### Step 3 — Classify security and exclusion

- **Security fix**: Confirm CVE and CVSS with the user or Security Authority before drafting. Do not speculate or include hints that could aid attackers. Some security fixes may be omitted from the published report — note that and recommend **ExcludeFromSUReport** when appropriate.
- **ExcludeFromSUReport**: Use **Tags** field only. Labels do **not** exclude from SU Report.

### Step 4 — Draft the release note

Apply all formatting and content rules in [references/guidelines-and-examples.md](references/guidelines-and-examples.md).

**Structure (prose only — no bullets or numbering in final text):**

1. Opening sentence — what was corrected or improved (past tense, positive, customer-facing).
2. Solution detail — how it was fixed at a high level.
3. Optional paragraphs — impacts, manual steps, performance, data tables, security (CVE/CVSS) as applicable.
4. Remove any template sections that do not apply; do not leave placeholder headings.

Run the quality checklist before presenting the draft.

### Step 5 — Quality checklist

Before showing the user:

- [ ] Past tense; describes what **was** fixed, not to-do actions
- [ ] Normal text style (no Heading styles — report tooling adds extra characters)
- [ ] Starts with a capital letter; no leading special characters or numbers
- [ ] No bullets, numbering, or list prefixes in the field content
- [ ] No prefixes: `Issue`, `Fix`, `Solution`, or variations
- [ ] No links to other Jira issues
- [ ] No customer or person names
- [ ] Focus on solution and impacts — not a detailed defect description
- [ ] Meaningful prose — not placeholder text (see unacceptable examples in reference)
- [ ] Spelling and grammar checked; tone is positive
- [ ] Security content is approved or flagged for Security Authority review
- [ ] Data table changes mentioned if applicable
- [ ] ExcludeFromSUReport recommended when justified

### Step 6 — Present draft and wait

Use the output template. **Stop.** Do not call `editJiraIssue` yet.

## Output Template (Show User First)

```markdown
## Release Notes Draft — {JIRA-KEY}: {summary}

**Release Notes field:**

{Plain prose release note — one or more paragraphs, no bullets}

**Bug correction impact:** {None \| brief summary for user review — merge into prose above when updating Jira}

**Manual steps required:** {None \| brief summary — merge into prose above when updating Jira}

**Data table changes:** {None \| tables affected}

**Security:** {N/A \| CVE, CVSS, and approved wording — or "Requires Security Authority approval"}

**ExcludeFromSUReport:** {No \| Yes — reason}

---
**Approve Jira update?** Reply **yes** / **no** / **edit** (with changes).
```

The auxiliary lines above are for review only. The text written to Jira must be a **single coherent prose block** (plus optional separate paragraphs), not labeled sections.

## Updating Jira (After Approval Only)

### Step A — Resolve field IDs

```
getJiraIssueTypeMetaWithFields
  cloudId: "ifsdev.atlassian.net"
  projectIdOrKey: "<project from issue key>"
  issueTypeId: "<Defect issue type id from getJiraIssue>"
```

Locate **Release Notes** (and **Tags** if applying ExcludeFromSUReport). If unclear, fetch the issue with `fields: ["*all"]` and inspect custom field names.

### Step B — Update fields

```
editJiraIssue
  cloudId: "ifsdev.atlassian.net"
  issueIdOrKey: "<JIRA-KEY>"
  fields: { "Release Notes": "<draft prose>", ... }
  contentFormat: "markdown"
```

Set **Release Notes** to the approved prose. Apply **ExcludeFromSUReport** in **Tags** only if the user confirmed.

### Step C — Confirm to user

Fetch the issue again and show the Release Notes (and Tags if changed). Report any field update errors.

## Relationship to Other Skills

- **ifs-jira-rca** — Root Cause Analysis (separate tab/fields; do not duplicate RCA narrative in Release Notes)
- **ifs-jira-reader** — Reading ticket context
- **ifs-ebr-compliance** — Data table / schema change details when drafting data-impact wording

## Additional Resources

- [Guidelines & examples](references/guidelines-and-examples.md) — IFS formatting rules, unacceptable content, good/bad examples
