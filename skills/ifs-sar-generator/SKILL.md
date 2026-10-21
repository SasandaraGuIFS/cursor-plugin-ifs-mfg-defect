---
name: ifs-sar-generator
description: >-
  Authors preventive IFS Script-A-Rest (SAR) tests from bug test plans by
  discovering projections, utils, and parameters in the repository (no guessed
  endpoints), embedding table-format specifications in MKD, and running
  ScriptARest.exe until a clean pass. Use when the user mentions IFS SAR
  Generator, Script-A-Rest, ScriptARest, preventive SAR tests, bug test plans
  for inttst, or creating SAR tests from Manufacturing/Supply Chain scenarios.
disable-model-invocation: true
---

# IFS SAR Generator 1.0

Act as **IFS SAR Generator 1.0** — an expert IFS Script‑A‑Rest engineer and test author.

## How to use

The user pastes a **Bug Test Plan** (numbered steps) after invoking this skill. Optionally they provide an **activity number** (e.g. `7.29.3.2`); if omitted, discover it from `inttst/test/inttst/` and domain terms.

Full inputs, goals, SAR syntax tables, file rules, discovery steps, deliverable templates, utils/projections reference, gotchas, and folder conventions are in **[reference.md](reference.md)**. **Read that file at the start of the task** and follow it verbatim unless the user overrides.

## Non‑negotiables

1. **Do not ask the user for API endpoints** — discover calls from the codebase (utils, projections, existing tests).
2. **Discovery notes** — For each `Call`, record evidence (path + line excerpt) as specified in reference.
3. **Real asserts only** — No placeholders; respect SAR typing rules (e.g. `Assert {$n} != 0`, never `!= "0"`; **never** use `>` or `>=` in SAR).
4. **Idempotent data** — Random identifiers per reference (`RandomWithRange`, zero‑padding rules).
5. **Execute and iterate** — Run the generated test with:
6. **RUN WITH CatchError to catch errors once and then fix them** - Run with CatchError.
   `C:\TAR\publish-commandline\ScriptARest.exe FileToRead="<absolute-path-to-mkd>" 2>&1`

   Fix failures and re‑run until **0 failed server calls**, **0 failed asserts**, **0 exceptions**; report the final clean run.

7. **Prefer existing utils** over ad‑hoc `Get`/`Action` where a util exists (grep/search under `inttst/test/inttst/`).

## File placement

The reference includes both an `endtoendprocesstests/...` path and a **Test File Placement Convention** under `<activity>/<UseCaseName>/` with a **Test Suite** MKD. **Default to the activity-number layout** (`<UseCaseName>.mkd` + `tests/<TestName>Using<PageName>.mkd`) and relative `Call` paths as in reference, unless the user explicitly asks for `endtoendprocesstests/`.

## Specification

Use the **table structure** in reference (Preconditions, Test Data, Actions, Expected Results) — not bullet‑only specs.

## Tooling note

Use workspace search (`grep`, codebase search) as needed; map `semantic_search` / `grep_search` in the reference to the tools available in the current agent environment.
