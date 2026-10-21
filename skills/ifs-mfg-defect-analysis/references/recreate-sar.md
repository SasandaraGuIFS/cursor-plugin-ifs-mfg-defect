# Recreate SAR — from scratch with asserts

Product-defect path only. This **ticket chat** authors a SAR that builds the scenario from scratch, **asserts the bug**, runs until green, then continues. After the fix is deployed, author a **separate Verify SAR** (same folder, same setup) that proves the correct behaviour. Do not overwrite the Recreate MKD.

This is **not** Step 7. Step 7 is the standalone fix suite under `docs/<KEY>/sar/` (after scanning `inttst`). Recreate lives under `docs/<KEY>/recreate/`.

Do **not** hand off a second chat. Do **not** use standalone-fix-sar or SAR-FDA for recreate. Do **not** invent REST endpoints.

Author and run using **manufacturing-sar-agent** + **ifs-sar-generator** rules (Eval/Assert alignment, `*Response` captures, discover utils from the repo, run ScriptARest until green). Placement and env below override those skills’ `inttst` / MFU1 defaults.

## Recreate (show the bug)

1. Author one MKD under `docs/<KEY>/recreate/Recreate<ShortName>.mkd`. Add `docs/<KEY>/recreate/util/` only when an `inttst` util cannot be used as-is.
2. Build **from scratch**: new parts and transactional data; reuse only environment basic data. Compact bug-id keys (`MFZ-30650` → `MFZ30650-#####`). Leave system-assigned shop order / DOP numbers alone.
3. Include **asserts that prove the bug exists** (wrong value, wrong state, error, duplicate line — whatever the ticket is). Query the bug-visible records, then Assert.
4. Run ScriptARest on **one** MASTER CMB as `alain` / `alain`. Prefer MASTER DEV CMB; if it is down, MASTER DEP CMB. Record which one in `docs/<KEY>/analysis.md`.
5. If the run fails for harness reasons (bad util, 401, missing basic data, wrong endpoint): **fix the SAR and re-run** on that same env until it runs properly (0 failed server calls **and** bug asserts pass).
6. Bug asserts passing **is** the recreate check. Do **not** wait for the user. Continue to the functional summary and draft fix.

## After the fix (show the fix)

Author a **second** file: `docs/<KEY>/recreate/Verify<ShortName>.mkd`. Prefer a shared `recreate/util/` for the from-scratch setup so Recreate and Verify do not duplicate the data chain.

- Recreate run (unfixed): `Recreate<ShortName>.mkd` — setup + **bug asserts** must pass. Leave this file unchanged after the fix.
- Verify run (Step 5b, fixed): `Verify<ShortName>.mkd` — same setup + **fix asserts** must pass.

Run Verify on the **same** MASTER CMB that recreated the bug. After the DUT is deployed, Recreate bug asserts are expected to fail on that env; only Verify is required to stay green.

## Environment (ScriptARest)

`ServerUrl` is the **origin only**. Strip `/main/ifsapplications/web/` (Aurena path, not SAR). Hosts from `docs/bnd-environment-urls.md` and `docs/bnd-environment-connections.json` — do not invent:

| Env | When | ServerUrl |
| --- | --- | --- |
| MASTER DEV CMB | prefer | `https://ifsmasterbnddevcmb.rnd.ifsdevworld.com` |
| MASTER DEP CMB | fallback if DEV is down | `https://ifsmasterbnddepcmb.rnd.ifsdevworld.com` |

- `Connect alain`
- Username / password: `alain` / `alain`
- Do not run recreate on Bnt.
- Do not require both DEV and DEP.

## Shape (copy these examples)

Keep this skeleton and **add** Asserts (the examples currently have none).

- `docs/MFZ-30650/recreate/RecreateIssuedPhantomCcr.mkd` — `mode: Standalone`, `owner: Manufacturing`, spec table, `Connect alain`, reuse site/company/location/customer/family, `MFZ30650-T/P/C` + `RandomWithRange`, `Call ../../../inttst/test/inttst/...`, `ApplyJson` + `Output` keys.
- `docs/MFZ-31069/recreate/RecreateDuplicateMaterialLinesUpdateSupplyConfig.mkd` — prefer this frontmatter: `type: Recreate SAR`. Local `recreate/util/` when needed. GET the bug-visible records at the end.

### Frontmatter

```yaml
---
type:  Recreate SAR
owner: Manufacturing
mode:  Standalone
---
```

### Calls

- From `docs/<KEY>/recreate/`: `../../../inttst/test/inttst/<activity>/...`
- Local util: `util/<Name>.mkd`

Typical util chain (skip unused layers): part catalog → inventory part → structure/routing → config if needed → shop order and/or DOP (and CO/pegging if that is the path).

## Data policy

### Reuse — environment basic data

Confirm values that already exist. Do not create these unless a util is only used to look them up.

Typical: Site, Company, Location No, Sales Price Group, Sales Group, Configuration Family, work center / labor class / inventory UoM.

**Customer, Persons, Supplier:** reuse when that party already works for the scenario. Create a dedicated one only when required (bug-id identifier).

Do **not** reuse as SAR inputs: part catalog / inventory / configured parts, product structures, routings, shop orders, DOP headers, material lines, or other transactional keys.

Do not ask the user for existing part numbers unless the ticket is *about* a specific catalog part that cannot be recreated — then document that as a gap.

### Identifier convention

- Compact prefix: `MFZ-30650` → `MFZ30650`.
- Agent-chosen fields (part no, descriptions, new customer/person/supplier): bug id + optional role letter + random suffix. Stay within IFS length limits (part no typically 25).

```
Eval RandomWithRange(10000, 99999).ToString()                       Into suffix
Eval "MFZ30650-T-" + suffix                                         Into topPartNo
```

- System-assigned numbers (shop order no, DOP id): leave them. Optionally put the bug id in a description.

## What not to do

- Do not write `docs/<KEY>/recreate/TEST-PLAN.md` as a required artefact.
- Do not treat SQLcl inspect or a random existing shop order as the primary seed.
- Do not drive the last user-visible action in Playwright to prove the bug (asserts do that).
- Do not place files under `inttst/`.
- Do not invent REST. Do not use standalone-fix-sar or SAR-FDA for this path.

## Support-track copies (ifs-track-backport)

When a previous-track run needs MKD edits, **leave the master Recreate and Verify files unchanged**. Copy the **Verify** SAR (and local `recreate/util/` if used) to `docs/<KEY>/recreate/<TRACK>/` and correct only that copy (add one `../` on relative `Call`s). See `ifs-track-backport`.
