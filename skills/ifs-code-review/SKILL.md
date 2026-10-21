---
name: ifs-code-review
description: This skill should be used after devising a solution or development plan, before presenting it to the user. It validates the proposed changes against IFS code review standards covering all file types (.plsql, .plsvc, .views, .projection, .client, .entity, .storage, .cdb, .upg, .pltst, .mkd). Run this checklist to catch issues before the user reviews the proposal.
---

# IFS Code Review Checklist

This skill validates a proposed solution against IFS code review standards. Run the checklist after architecting a fix or development — before presenting it to the user. Flag any violations or concerns.

## When to Use

After completing the solution design (Phase 3 of `/fix-defect` or `/develop`), before presenting the final output. Validate every proposed file change against the relevant checklist.

## Quick Validation Checklist

For every proposed change, verify these **mandatory** items:

### All Files
- [ ] History comment added (YYMMDD Sign Ticket format, newest at top, matching file's spacing)
- [ ] Bug tags present on support tracks (24R1–26R2); not on master (27R1)
- [ ] EBR compliance on 25R2+ tracks (no direct `_RTB` references in app code; `#`-marked methods in `.ddlsource`/`.dmlsource`)
- [ ] No spelling errors in file names, variable names, constructs
- [ ] No hard-coded values — use constants or enumeration DB values

### PL/SQL (.plsql)
- [ ] No API-breaking changes (no removed/renamed methods or parameters on support tracks)
- [ ] Default values added when adding new parameters to existing methods
- [ ] No enumeration client values reaching server code — use DB values
- [ ] No duplicate error messages
- [ ] No API calls inside cursors
- [ ] No direct table INSERT/UPDATE/DELETE — use framework CRUD methods
- [ ] Proper exception handling
- [ ] Unit test added or `@IgnoreUnitTest` annotation with reason
- [ ] Variables use `%TYPE` / `%ROWTYPE` where possible
- [ ] Cursors closed after use

### PLSVC (.plsvc)
- [ ] Logic belongs at plsvc level (not better placed in .plsql)
- [ ] No direct table/private view access outside the component
- [ ] Correct dynamic component dependencies
- [ ] No SQL injection risk (use bind variables)

### Views (.views)
- [ ] Correct stereotype (Private, Public, LOV) with proper suffix
- [ ] Column properties align with entity column properties
- [ ] Security check tags present (`@SecurityCheck`)
- [ ] No `&` sign inside comments

### Projection (.projection)
- [ ] Name meaningful with proper suffix (Handling, Analysis, etc.)
- [ ] Entity/query keys match model entity
- [ ] No duplicated attributes or references
- [ ] Boolean attributes with API fetch have defaults via `CRUD_Default___`
- [ ] Dynamic dependencies set correctly
- [ ] Security: bounded actions used; initial check properly set
- [ ] Performance: avoid Get methods in fetch attributes; avoid expensive ARRAY JOINs

### Client (.client)
- [ ] Name aligned with projection name
- [ ] Navigator entry and page label correct
- [ ] Dynamic dependencies set for dynamic elements
- [ ] Server calls optimized (bundled where possible)

### Entity (.entity)
- [ ] Correct composite key and parent keys
- [ ] Proper field types, sizes, and attribute flags
- [ ] Row level security added
- [ ] Labels self-explanatory

### CDB/UPG (.cdb, .upg)
- [ ] CDB is redeployable
- [ ] DML operations followed by COMMIT
- [ ] Support CDB files contain only `Database_SYS` calls
- [ ] No interaction with dynamic components
- [ ] Code efficient for large data volumes

### Storage (.storage)
- [ ] Indexes reference `_rtb` on EBR tracks (25R2+)
- [ ] Indexes, temp tables, sequences in proper format

### Tests (.pltst)
- [ ] Tests behavior, not implementation
- [ ] All input/output combinations including NULL
- [ ] Meaningful test name
- [ ] SYSDATE used as constant, not called repeatedly

### REST Tests (.mkd)
- [ ] Happy path + positive/negative paths covered
- [ ] Test is rerunnable and parallel-safe (random keys)
- [ ] No `Delay` or `Print` commands
- [ ] Use `Create`/`Modify`/`Action` instead of `Post`/`Patch`
- [ ] Utils do NOT contain Asserts
- [ ] GET requests fetch only required attributes

## How to Report

When validating, output a brief compliance summary:

```
## Code Review Compliance

### Passed
- History comments: Added to all 3 files
- Bug tags: Correctly applied (25R2 track)
- EBR: No _RTB references in app code
- Tests: Unit test added for new method

### Flagged
- ⚠ Projection: Boolean attribute `IsActive` has API fetch but no CRUD_Default___ default
- ⚠ PLSQL: Cursor `get_data` not closed on exception path
```

Only flag actual issues — don't list every passing check.

## Additional Resources

### Reference Files

For the complete file-type-specific checklists with all basic and extended checks:
- **`references/file-type-checklists.md`** — Full checklists for Entity, PLSQL, PLSVC, Views, Projection, Client, CDB/UPG, Storage, PLTST, Script-A REST tests, and General checks. Sourced from the [SC Code Review Checklist](https://ifsdev.atlassian.net/wiki/spaces/SC/pages/1097629802) and the SE Code Review Checklist spreadsheet.
