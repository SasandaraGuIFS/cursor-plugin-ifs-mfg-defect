# Root Cause Analysis — Themes, Guidelines & Jira Fields

Source: IFS Engineering Excellence — Root Cause Analysis How To's

## Why RCA?

Understanding underlying reasons for defects helps move beyond symptoms to fix root causes and prevent recurrence. RCA supports the Zero Defects initiative.

## Three Questions Every RCA Must Answer

1. **What is the underlying problem?**
2. **Why couldn't we detect this defect before releasing?**
3. **How can we prevent similar issues happening in future?**

## When RCA Is Required

- All customer-reported defects
- All internal P1 and P2 defects reported after Implementation Complete
- CCB out-of-band corrections and CCRs

Current focus: IFS Cloud tracks.

## Root Cause Theme & Sub-theme Taxonomy

Use **Root Cause Theme** in Jira for theme + sub-theme. Use **Root Cause** field for detailed findings.

| Main Theme | Sub Theme | Root Cause Examples |
|---|---|---|
| **Process** | UX Design | Persona not identified. / Jobs to be done not identified. / Usability testing was not carried out |
| | Acceptance Criteria | Functional action was missing in acceptance criteria of the user story where this defect was introduced / Incorrect acceptance criteria of the user story where this defect was introduced |
| | Developer Analysis | Performance impact was not considered as part of the scope / Security impact was not considered as part of the scope / Defect is unintended consequence of implementation / Defect could have been avoided if standards/principles followed. / Very sensitive part of code base was refactored, but the risk was underestimated. |
| | Test Strategy | Automated tests only covered happy path / Manual test plan did not cover this scenario / Gap in boundary value testing |
| | Estimation & Planning | Time to complete TAR tests was not included in planning / Development time underestimated, so not enough time to complete work / Development tasks not broken down into smaller, testable elements, so difficult to test all scenarios |
| | Documentation | Missing or incorrect end-user documentation, technical documentation or enablement material |
| | Other | |
| **Tools** | Static Code Analysis Tools | Defect could have been detected by Static Code Analysis. / Gap in the tool or proper tool is not used. |
| | Unit Testing Tools | Defect could have been detected by a unit test, but test couldn't be written due to a gap in the tool. |
| | UI Testing Tools | Defect could have been detected by a UI test, but test couldn't be written due to a gap in the tool. |
| | Integration Testing Tools | Defect could have been detected by an integrated test, but test couldn't be written due to a gap in the tool. |
| | Jira | An important check is missing in DoR/DoD or Jira workflow |
| | Confluence | An important check is missing in gate review check lists |
| | Other | |
| **Reasonable Defect** | Infrastructure/Hardware | Issue is a result of a malfunction or a failure in infrastructure or hardware like Azure, Git, VMs, JFrog, etc. |
| | Exceptional | Issue is caused by an exceptional combination of functional flow and data. It's unlikely that a similar issue is happening again |

### Theme Selection Guidance

- Prefer the **most specific** sub-theme that fits the evidence.
- **Process → Developer Analysis** — logic error, missed edge case, standards not followed, unintended side effect of implementation.
- **Process → Test Strategy** — defect could have been caught by existing test types but scenario was not covered.
- **Tools → Unit/Integration/UI Testing Tools** — test *could* have caught it but tooling gap prevented writing the test.
- **Reasonable Defect → Exceptional** — rare data/flow combination; unlikely to recur.
- Use **Other** only when no sub-theme fits; explain in the Root Cause text.

## Preventive Action Rules

| Root Cause Theme | Preventive Action |
|---|---|
| **Process** | **Required** — eliminate or minimize recurrence |
| **Tools** | **Required** — eliminate or minimize recurrence |
| **Reasonable Defect** | Recommended but not mandatory |

Preventive actions may be:
1. **Completed with the fix** — record in the **Preventive Action** field on the Root Cause Analysis tab.
2. **Planned separately** — create a linked **Preventive Action** issue type (via transition checkbox or manual create + link).

A defect may have multiple preventive actions. All Preventive Action issues must link to at least one Defect.

## Introduced In Field

Records the **timeframe** when the defect was introduced (not the reported version).

**Options:** Half-year codes (e.g. `26-H1`, `26-H2`), `Pre-Existing` (before 2023), `Unknown` (cannot determine within ~1 hour).

**Rules:**
- Select the **development half** when the bug was introduced, regardless of Reported Version.
- Example: reported in 23-H2 for 21R2 but introduced in 23-H1 → select `23-H1`.
- Issues introduced before 2023 → `Pre-Existing`.
- If investigation exceeds ~1 hour to determine → `Unknown`.
- Mandatory for customer-reported Defects when Change Type = Correction.
- Not required for cloned (FixCopy) issues — complete on the original.

## Jira Fields (Root Cause Analysis Tab)

| Jira Field | Purpose |
|---|---|
| **Introduced In** | Timeframe of introduction |
| **Root Cause Theme** | Theme and sub-theme selection |
| **Root Cause** | Detailed RCA narrative |
| **Preventive Action** | Actions completed while fixing the issue |

## Useful Links

- [RCA Report (Power BI)](https://app.powerbi.com/groups/f73223e4-d5cb-4448-9ac5-6bd692b36c8e/reports/4252303b-8203-426d-85a2-3daf25f85ea0)
