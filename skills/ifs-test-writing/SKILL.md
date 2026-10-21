---
name: ifs-test-writing
description: This skill should be used when writing, reading, or modifying IFS Cloud PL/SQL unit tests (.pltst files), creating @MockTable or @MockPackage definitions, writing ASSERT statements, or adding test coverage for a defect fix.
---

# IFS Test Writing (.pltst)

This skill provides the syntax and patterns for IFS Cloud PL/SQL unit tests. `.pltst` files live at `test/<component>/database/`.

## UNITTEST Structure

```sql
UNITTEST "Description of what is being tested" FOR
   FUNCTION|PROCEDURE Name (param_ IN TYPE, ...) [RETURN type];
USING
   [variable declarations]
   [@MockTable directives]
   [@MockPackage directives]
   [@Mock directives]
IS
   [test local variables]
BEGIN
   FOR
      | expected_ | param1_ | param2_ |
      | value     | arg1    | arg2    |
   LOOP
      [call the function/procedure]
      [ASSERT statements]
   END LOOP;
END UNITTEST;
```

## Key Sections

| Section | Purpose |
|---------|---------|
| `UNITTEST ... FOR` | Declares what function/procedure is being tested |
| `USING` | Mock definitions and shared test variables |
| `IS ... BEGIN` | Test-local variable declarations and execution |
| `FOR ... LOOP` | Parameterized test data — one iteration per row |
| `ASSERT` | Validates expected vs actual result |

## Mock Types

### @MockTable — Mock a database table

Provide test data for a `_tab` table. Columns are pipe-delimited.

```sql
@MockTable pers_supervisor_assignment_tab
VALUES
   | team_id | supervisor_id | valid_from                          |
   | 'TEAM1' | 'SUP1'        | TO_DATE('01/01/2022', 'dd/mm/yyyy') |
   | 'TEAM2' | 'SUP2'        | TO_DATE('01/01/2023', 'dd/mm/yyyy') |
END VALUES;
```

Multiple `@MockTable` directives can appear in one UNITTEST.

### @MockPackage — Mock an external package

Mock a function/procedure from another LU/component. Signature must match the original exactly.

```sql
@MockPackage Access_Setup_Configuration_API
FUNCTION Is_Team_Setup_Valid(
   person_id_ IN     VARCHAR2) RETURN NUMBER   IS
BEGIN
   IF person_id_ = 'PER5' THEN
      RETURN 0;
   ELSE
      RETURN 1;
   END IF;
END Is_Team_Setup_Valid;
```

Mock bodies can contain conditional logic (IF/ELSIF/ELSE) and can return test variables that change per loop iteration.

### @Mock — Mock a local function (same LU)

Same as `@MockPackage` but for functions within the LU being tested.

```sql
@Mock
FUNCTION Get_Duration (
   company_id_ IN     VARCHAR2) RETURN NUMBER
IS
BEGIN
   RETURN duration_;
END Get_Duration;
```

### @MockPackage ERROR_SYS — Test error conditions

When testing procedures that raise errors, mock `ERROR_SYS.Record_General` and assert inside the mock:

```sql
@MockPackage ERROR_SYS
PROCEDURE Record_General (
   lu_name_  IN     VARCHAR2,
   err_text_ IN     VARCHAR2,
   p1_       IN     VARCHAR2 DEFAULT NULL,
   p2_       IN     VARCHAR2 DEFAULT NULL,
   p3_       IN     VARCHAR2 DEFAULT NULL )
IS
   expected_ VARCHAR2(1000) := 'ERRTAG: Expected error message :P1.';
BEGIN
   ASSERT err_text_ = expected_ MESSAGE 'Unexpected error: '|| err_text_;
END Record_General;
```

## FOR Loop — Parameterized Test Data

```sql
FOR
   | expected_ | company_id_ | emp_no_ |
   | 'TRUE'    | 'GTECH'     | 'WALT'  | -- Has non-primary jobs
   | 'FALSE'   | 'A1A'       | 'HANK'  | -- Only primary
   | NULL      | 'XXX'       | 'NONE'  | -- Nonexistent
LOOP
   return_ := Function_Name(company_id_, emp_no_);
   -- assert here
END LOOP;
```

- First row = column headers (variable names)
- Subsequent rows = test data (one test case per row)
- Trailing comments after `|` are allowed

## Data Types in Test Tables

| Type | Syntax |
|------|--------|
| VARCHAR2 | `'value'` |
| NUMBER | `1`, `0`, `99999` (no quotes) |
| DATE | `TO_DATE('01/01/2024', 'dd/mm/yyyy')` |
| BOOLEAN | `TRUE` / `FALSE` (no quotes in FOR; `1`/`0` in _tab mocks) |
| NULL | `NULL` keyword |
| Empty string | `''` |

## Assertion Patterns

### Simple equality
```sql
ASSERT return_ = expected_ MESSAGE 'Expected '||expected_||' but returned '||return_;
```

### NULL-aware (use when return can be NULL)
```sql
IF expected_ IS NULL AND return_ IS NULL THEN
   ASSERT TRUE;
ELSE
   ASSERT return_ = expected_ MESSAGE 'Expected '||expected_||' but returned '||return_;
END IF;
```

### NULL-aware verbose
```sql
IF expected_ IS NOT NULL THEN
   ASSERT return_ = expected_ MESSAGE 'Expected '||expected_||' but returned '||return_;
ELSE
   IF return_ IS NULL THEN
      ASSERT TRUE;
   ELSE
      ASSERT FALSE MESSAGE 'Expected NULL but returned '||return_;
   END IF;
END IF;
```

## File Template

```sql
layer Core;

@OptionalMocks

-------------------- LU SPECIFIC IMPLEMENTATION METHODS ---------------------

-------------------- LU SPECIFIC PUBLIC METHODS -----------------------------

UNITTEST "Description" FOR
   FUNCTION Method_Name (...) RETURN type;
USING
   -- mocks here
IS
   return_   type;
   expected_ type;
BEGIN
   FOR
      | expected_ | param_ |
      | value     | arg    |
   LOOP
      return_ := Method_Name(param_);
      ASSERT return_ = expected_ MESSAGE 'Expected '||expected_||' but returned '||return_;
   END LOOP;
END UNITTEST;
```

## When to Write Tests

- When fixing a defect: add test cases that reproduce the bug and verify the fix
- When adding a new public method: cover primary scenarios, edge cases, and NULL inputs
- When modifying validation logic: add cases for the new validation rules

## Writing Tips

1. **Read the existing .pltst file first** — add new UNITTESTs at the bottom, matching the file's style
2. **Mock only what's needed** — mock external APIs and tables used by the function under test
3. **Include edge cases** — NULL parameters, empty strings, nonexistent records, boundary dates
4. **Use trailing comments** on test rows to explain what each case tests
5. **Test both positive and negative** — expected successes and expected failures/NULLs
6. **For procedures that raise errors** — mock ERROR_SYS and assert inside the mock body
7. **Use hard-coded dates** instead of SYSDATE in test data to avoid flaky tests

## Additional Resources

### Reference Files

For complete real-world examples from the person component:
- **`references/pltst-examples.md`** — Full UNITTEST examples covering @MockTable, @MockPackage, @Mock, BOOLEAN returns, error validation, NULL handling, combined mocks with test comments
