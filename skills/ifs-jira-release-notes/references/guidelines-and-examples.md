# IFS Release Notes — Guidelines and Examples

Official rules for the Jira **Release Notes** field on Defect issues. This field is mandatory when closing an issue.

## Purpose

Record in Jira high-level details regarding the issue, solution, and impacts of the issue correction. Also include additional steps or manual interventions required for the fix to be implemented, if applicable. For security-related fixes, include CVE and CVSS scores, as well as other approved security-related information. Any changes made to data tables should also be mentioned.

The Release Notes field in Jira is mandatory when closing an issue, and it should be filled according to the following guidelines. It is very important to think from a customer's point of view. The release note must have information for a customer to understand how a reported defect was fixed, including details of performance enhancement (if done).

**IMPORTANT:** Please use the **ExcludeFromSUReport** option in the **Tags** field in the Jira issue if certain fix information needs to be excluded in the Service Update report or the New Patch Report for APP10 from Jira for some justifiable reason. Please do **NOT** use the **Labels** field as this will not exclude the issue from the SU Report.

## Formatting Rules

Content should be written in past tense since it describes what has been fixed. It should not be written as a "To Do" action list.

Do not use bullets or numbering for your content.

Ensure the text style is "Normal text" and not any version of "Heading" as the report inserts extra characters if "Heading" style is selected.

Start with a Capital letter.

Do not prefix the content with any special characters or numbers.

Remove the sections of the template that are not relevant.

This field is extracted and published in the Service Update Fixes Report. Starting UPD25, this field is being extracted and published as the Patch Report for APP10. Therefore, the content should be meaningful for the customers and easy for them to read and understand.

Ensure correct spelling and grammar.

Write the content in a positive manner.

Do not enter detailed description of the issue — instead write only about the solution, what was done to fix the issue.

Do not include links to other issues in the Release Notes field.

Do not prefix your content using the following:

- `Issue` or any variation
- `Issue:`
- `Fix:`
- `*Fix` or any variation
- `Solution:`

Do not include names of the customers or persons.

Include high level details of the solution, and bug correction impacts, providing additional steps or manual interventions required for the fix to be available, if any. If the fix is security related, the CVE and CVSS scores, and other security related information should be included.

## Bug Correction Impact

If applicable, mention changes done to the data tables.

Describe customer-visible or operational impacts of the correction — for example, changed calculation results, corrected default behavior, or required re-processing — in plain language.

## Security-Related Fixes

Content of Security fixes should be approved by the relevant Security related Authorities to ensure that we do not give hints even by mistake to the hackers. Please contact your manager if you are not sure about the Security Authorities.

Security related fixes should include the CVE and CVSS scores. Please contact the Security related Authority to determine the CVE and CVSS scores if you are not sure to determine it.

There could be scenarios where due to security reasons, we may avoid including a particular security related fix in the report.

Please refer **Guidelines for Secured Information on Technical Documentation** for further details.

When drafting, flag unapproved security wording for review rather than inventing CVE/CVSS values.

## Unacceptable Content

The following are examples of unacceptable content:

- "It is fixed".
- "It was fixed in App10, now merged to IFS Cloud".
- "The issue has been taken care of now".
- Blanks
- "."
- "-"
- "N/A"
- "Fixed"
- Retaining the default content
- "Completed in all tracks"
- Links to other issues

## Good Examples

### Example 1 — Functional correction (no manual steps)

The labor time registration for shop order operations was corrected so that reported hours are stored with the correct operation reference when multiple outside operations exist on the same shop order. Operations labor history now displays the expected time entries for each operation without requiring any customer configuration changes.

### Example 2 — With manual intervention

The purchase order receipt validation was updated to accept partial receipts when the supplier delivery note quantity differs from the ordered quantity within configured tolerance limits. After applying this update, existing receipt lines that were blocked before the correction must be re-validated from the Receive Purchase Order page to complete the receipt.

### Example 3 — Performance enhancement

The shop order operation list query was optimized to reduce database round-trips when loading operations for large shop orders. Users will notice faster page load times when opening shop orders with many operations, with no change to displayed data or required setup.

### Example 4 — Data table change

The correction updated how default values are initialized for new records in the related configuration table during upgrade. Existing stored data was not modified automatically; sites that relied on the previous default must review and update configuration once after the service update is applied.

### Example 5 — Security fix (illustrative — requires Security Authority approval)

A security vulnerability (CVE-2026-12345, CVSS 7.5) in document attachment handling was remediated by strengthening access validation before files are retrieved through the affected API. No customer manual steps are required beyond applying the service update containing this correction.

## Bad Examples

### Too vague

Fixed.

### Restates the issue instead of the solution

Users reported that labor hours were wrong on shop orders with outside operations. The hours did not match what was entered.

### Uses forbidden prefixes and bullets

Fix: Updated the validation.
- Changed the API
- Added a test

### Internal / track boilerplate

It was fixed in App10, now merged to IFS Cloud. Completed in all tracks.

### Links and names

See MFZ-29800 for related work. Reported by Contoso Ltd.

## Agent Drafting Tips

1. **Lead with the customer benefit** — what works correctly now or what improved.
2. **One idea per paragraph** — keeps prose readable without bullets.
3. **Manual steps last** — after the solution, state clearly if the customer must act post-update.
4. **Data impacts** — name tables or data areas only at the level customers need (not internal package names).
5. **Pair with RCA skill** — technical root cause belongs in RCA fields, not Release Notes.
6. **When unsure on security** — draft non-sensitive high-level wording and ask the user to obtain Security Authority approval before Jira update.
