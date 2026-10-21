# Resume file — `docs/<KEY>/analysis.md`

Create this on first run for the ticket. Update after every step. RCA and Release Notes are drafts only (no Jira write, no approval gate).

```markdown
# <KEY> — analysis state
Track: <resolved track> | Verdict: <pending | intended design | product defect>

- [ ] 1 Attachments processed
- [ ] 1 Plain explanation + example
- [ ] 2 Similar Jira searched
- [ ] 3 Docs + code proof
- [ ] 4 WAD comment drafted  (intended-design path; chat / analysis.md only — do not write Jira)
- [ ] 4 Recreate SAR authored (`docs/<KEY>/recreate/`)
- [ ] 4 Recreate SAR green (bug asserts) on MASTER CMB
- [ ] 4 Created keys recorded
- [ ] 4b Functional investigation summary (1 paragraph)
- [ ] 5 Fix drafted + code review run
- [ ] 5b Fix applied + deployed
- [ ] 5b Unit tests for changed files (or none)
- [ ] 5b Verify SAR green (fix asserts) on same MASTER CMB
- [ ] 6 RCA draft (chat / analysis.md only — do not write Jira)
- [ ] 7 Matrix + SAR built (`docs/<KEY>/TEST-MATRIX.md` + `docs/<KEY>/sar/`, inttst dedup, RESULTS)
- [ ] 8 Release Notes draft (chat / analysis.md only — do not write Jira)
- [ ] 9 Master commit pushed (27R1) — only after user **yes**
- [ ] 10 Track backport pushed — only after user **yes**

## Notes per step

### 1
...

### 3 Proof
...

### 4 Recreate
Env (MASTER DEV CMB prefer, DEP fallback): ...
ServerUrl (origin only): ...
Connect user: alain
SAR MKD: docs/<KEY>/recreate/Recreate<ShortName>.mkd
Verify MKD: docs/<KEY>/recreate/Verify<ShortName>.mkd
SAR run: pass/fail + bug asserts
Created keys:

| Kind | Role | Value |
| --- | --- | --- |
| Part no | | |
| Customer / person / supplier | reused or created | |
| Shop order / DOP / CO | system-assigned | |
| Site and other basic data | reused | |

### 5 Fault / draft fix
...

### 5b Deploy / verify
Env (same as recreate): ...
Deploy result: ...
Unit tests: package / pass-fail / none
Fix asserts: pass/fail
Bug gone?: ...
...
```
