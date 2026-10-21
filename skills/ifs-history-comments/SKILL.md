---
name: ifs-history-comments
description: This skill should be used when adding history comments to IFS Cloud source files after making code changes, ensuring the correct YYMMDD Sign Ticket format is placed at the right location in .plsql, .plsvc, .views, .client, .fragment, .projection, and other file types.
---

# IFS History Comments

Every changed file in IFS Cloud must have a history comment added to the header block. This skill defines the exact format and placement rules.

## Format

```
--  YYMMDD  sign    TICKET, Description of change.
```

| Field | Format | Example |
|-------|--------|---------|
| Date | YYMMDD (6 digits) | `260324` = March 24, 2026 |
| Sign | Developer ID (6 chars) | `GUNSLK` |
| Ticket | Jira ticket ID | `HRZ-20567`, `HCMDEV-16493` |
| Description | Brief summary of what was changed | `Modified Check_Common___ to validate overlap.` |

## Ordering: Newest Entry at the TOP

History entries are ordered **newest first** — add new entries at the **top** of the history block, immediately after the header separator line (`--  ------  ------  ---...`).

## Placement

1. **Read the file header** — look at the first 15-20 lines to find the history block
2. **Find the separator line** — the dashed line after `Date  Sign  History` (e.g. `--  ------  ------  ---...`)
3. **Add the new entry immediately after the separator**, pushing existing entries down
4. **Copy the exact spacing** from the existing entries in that specific file — there is no universal spacing standard; it varies file to file

### File types with history headers

- `.plsql`, `.plsvc`, `.views` — Full structured header with Logical unit, Component, Template version
- `.client`, `.fragment`, `.projection` — May have a shorter header variant

### File types WITHOUT history headers

- `.entity` — XML format, no history comment block. No history comment needed.

## Rules

1. **Always add at the top** of the history block (newest first)
2. **Match the existing spacing** in the file — different file types use slightly different column alignment
3. **One entry per file per ticket** — even if multiple methods are changed, summarize in one history line
4. **Use today's date** in YYMMDD format
5. **Developer sign**: `slpelk`
6. **Include ticket ID** followed by comma, then description
7. **Description should summarize** what was changed: which methods were added/modified/removed, or what behavior changed
8. **Keep description concise** — one line, typically 60-100 characters

## Description Conventions

Common phrasing patterns:

```
--  260324  slpelk  HRZ-20567, Modified Check_Common___ to validate date overlap.
--  260324  slpelk  HRZ-20567, Added Get_Primary_Manager overload.
--  260324  slpelk  HRZ-20567, Removed obsolete Calculate_Rate___ method.
--  260324  slpelk  HRZ-20567, Created.
--  260324  slpelk  HRZ-20567, Modified LOV filter for EmployeeSelector.
--  260324  slpelk  HRZ-20567, Added new attribute InternalDisplayName to entity override.
--  260324  slpelk  HRZ-20567, Modified view Own_Activities_Calendar to fix date filter.
```

When multiple methods are changed in one file:
```
--  260324  slpelk  HRZ-20567, Modified Check_Insert___ and Check_Update___ to validate overlap period.
--  260324  slpelk  HRZ-20567, Added Validate_Overlap___, modified Check_Common___ and Prepare_Insert___.
```

## Workflow

When making a code change:

1. Read the first 15-20 lines of the file to see the existing history block
2. Identify the separator line (`--  ------  ------  ---...`)
3. Add the new entry on the line immediately after the separator, matching the file's spacing
4. Push all existing entries down by one line
5. Do this for **every** file modified as part of the fix
