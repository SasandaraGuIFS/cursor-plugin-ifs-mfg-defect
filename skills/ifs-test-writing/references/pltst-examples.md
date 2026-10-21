# IFS .pltst Test Examples — Detailed Reference

All examples sourced from `PersSupervisorAssignment.pltst` and other files in the `person` component.

## File Structure

```sql
-----------------------------------------------------------------------------
--  [history comments]
-----------------------------------------------------------------------------

layer Core;

@OptionalMocks

-------------------- LU SPECIFIC IMPLEMENTATION METHODS ---------------------

-------------------- LU SPECIFIC PUBLIC METHODS -----------------------------

[UNITTEST blocks here]
```

Note: `@OptionalMocks` annotation may appear after `layer Core;` — it allows tests to run even if some mocked dependencies are not available.

## Example 1: Simple Function Test with @MockPackage

Source: `PersSupervisorAssignment.pltst`

```sql
UNITTEST "Manual_Transaction_From should return transaction from date when assingment id is given" FOR
   FUNCTION Manual_Transaction_From (
      assignment_id_ IN     NUMBER) RETURN VARCHAR2;
USING
   @MockPackage Pers_Supervisor_Assignment_API
   FUNCTION Get_Transaction_From(
      assignment_id_ IN     NUMBER) RETURN DATE   IS
   BEGIN
      IF assignment_id_ = 1 THEN
         RETURN TO_DATE('01/01/2021', 'dd/mm/yyyy');
      ELSIF assignment_id_ = 2 THEN
         RETURN NULL;
      ELSE
         RETURN NULL;
      END IF;
   END Get_Transaction_From;
IS
   return_   VARCHAR2(2000);
   expected_ VARCHAR2(2000);
BEGIN
   FOR
      | expected_ | assignment_id_ |
      | 'TRUE'    | 1              |
      | 'FALSE'   | 2              |
      | 'FALSE'   | 3              |
      | 'FALSE'   | NULL           |
   LOOP
      return_ := Manual_Transaction_From(assignment_id_);
      ASSERT return_ = expected_ MESSAGE 'Expected '||expected_||' but returned '||return_;
   END LOOP;
END UNITTEST;
```

## Example 2: @MockTable with Dates

Source: `PersSupervisorAssignment.pltst`

```sql
UNITTEST "Get_Assignment_Start_Date should return supervisors assignment start date when supervisor information is given" FOR
   FUNCTION Get_Assignment_Start_Date (
      team_id_       IN     VARCHAR2,
      supervisor_id_ IN     VARCHAR2) RETURN DATE;
USING
   @MockTable pers_supervisor_assignment_tab
   VALUES
      | valid_from                                    | team_id | supervisor_id |
      | TO_DATE('01/01/2022', 'dd/mm/yyyy')           | 'TEAM1' | 'SUP1'        |
      | TO_DATE('01/01/2100', 'dd/mm/yyyy')           | 'TEAM1' | 'SUP2'        |
      | TO_DATE('01/01/2021', 'dd/mm/yyyy')           | 'TEAM2' | 'SUP1'        |
      | TO_DATE('10/01/2021', 'dd/mm/yyyy')           | 'TEAM2' | 'SUP1'        |
      | TO_DATE('01/01/2020', 'dd/mm/yyyy')           | 'TEAM2' | 'SUP2'        |
      | TO_DATE('01/01/2100', 'dd/mm/yyyy')           | 'TEAM2' | 'SUP2'        |
   END VALUES;
IS
   return_   DATE;
   expected_ DATE;
BEGIN
   FOR
      | expected_                                     | team_id_ | supervisor_id_ |
      | TO_DATE('01/01/2022', 'dd/mm/yyyy')           | 'TEAM1'  | 'SUP1'         |
      | TO_DATE('01/01/2100', 'dd/mm/yyyy')           | 'TEAM1'  | 'SUP2'         |
      | TO_DATE('01/01/2021', 'dd/mm/yyyy')           | 'TEAM2'  | 'SUP1'         |
      | TO_DATE('01/01/2020', 'dd/mm/yyyy')           | 'TEAM2'  | 'SUP2'         |
      | NULL                                           | 'TEAM3'  | 'SUP3'         |
      | NULL                                           | 'TEAM4'  | 'SUP4'         |
   LOOP
      return_ := Get_Assignment_Start_Date(team_id_, supervisor_id_);
      IF expected_ IS NOT NULL THEN
         ASSERT return_ = expected_ MESSAGE 'Expected '||expected_||' but returned '||return_;
      ELSE
         IF return_ IS NULL THEN
            ASSERT TRUE;
         ELSE
            ASSERT FALSE MESSAGE 'Expected '||'NULL'||' but returned '||return_;
         END IF;
      END IF;
   END LOOP;
END UNITTEST;
```

Key: NULL-aware assertion — explicit IF/ELSE to handle NULL comparison.

## Example 3: BOOLEAN Return Type

Source: `PersSupervisorAssignment.pltst`

```sql
UNITTEST "Is_Exist should check whether supevisor assignment exist for overlapping period" FOR
   FUNCTION Is_Exist (
      team_id_       IN     VARCHAR2,
      supervisor_id_ IN     VARCHAR2,
      person_id_     IN     VARCHAR2,
      valid_from_    IN     DATE,
      valid_to_      IN     DATE,
      assignment_id_ IN     NUMBER) RETURN BOOLEAN;
USING
   @MockTable pers_supervisor_assignment_tab
   VALUES
      | team_id | supervisor_id | person_id | valid_to                              | valid_from                             | assignment_id |
      | 'TEAM1' | 'SUP1'        | 'PER1'    | TO_DATE('31/12/2050', 'dd/mm/yyyy')   | TO_DATE('31/12/2010', 'dd/mm/yyyy')    | 1             |
      | 'TEAM1' | 'SUP1'        | 'PER1'    | TO_DATE('31/12/2030', 'dd/mm/yyyy')   | TO_DATE('31/12/2023', 'dd/mm/yyyy')    | 2             |
      | 'TEAM2' | 'SUP1'        | 'PER1'    | TO_DATE('31/12/2050', 'dd/mm/yyyy')   | TO_DATE('31/12/2010', 'dd/mm/yyyy')    | 4             |
   END VALUES;
IS
   return_   BOOLEAN;
   expected_ BOOLEAN;
BEGIN
   FOR
      | expected_ | team_id_ | supervisor_id_ | person_id_ | valid_from_                             | valid_to_                             | assignment_id_ |
      | TRUE      | 'TEAM1'  | 'SUP1'         | 'PER1'     | TO_DATE('01/01/2050', 'dd/mm/yyyy')     | TO_DATE('31/12/2050', 'dd/mm/yyyy')   | 12             |
      | FALSE     | 'TEAM1'  | 'SUP1'         | 'PER1'     | TO_DATE('01/01/2050', 'dd/mm/yyyy')     | TO_DATE('31/12/2050', 'dd/mm/yyyy')   | 1              |
      | FALSE     | 'TEAM1'  | NULL           | NULL       | TO_DATE('01/01/2050', 'dd/mm/yyyy')     | TO_DATE('31/12/2050', 'dd/mm/yyyy')   | 15             |
   LOOP
      return_ := Is_Exist(team_id_, supervisor_id_, person_id_, valid_from_, valid_to_, assignment_id_);
      ASSERT return_ = expected_ MESSAGE 'Expected '||expected_||' but returned '||return_;
   END LOOP;
END UNITTEST;
```

Key: BOOLEAN expected/return values use `TRUE`/`FALSE` directly (no quotes) in the FOR table.

## Example 4: @MockTable + @MockPackage Combined

Source: `PersSupervisorAssignment.pltst`

```sql
UNITTEST "Get_Primary_Manager should return the primary manager of the person" FOR
   FUNCTION Get_Primary_Manager(
      person_id_      IN     VARCHAR2,
      date_           IN     DATE DEFAULT sysdate,
      team_id_        IN     VARCHAR2 DEFAULT NULL,
      validate_setup_ IN     BOOLEAN DEFAULT TRUE) RETURN VARCHAR2;
USING
   @MockTable pers_supervisor_assignment_tab
   VALUES
      | supervisor_id | valid_from                               | valid_to                                 | person_id | primary_manager | team_id |
      | 'SUP1'        | TO_DATE('16-10-2025','DD-MM-YYYY')       | TO_DATE('16-10-2025','DD-MM-YYYY')       | 'PER1'    | 1               | 'TEAM1' |
      | 'SUP1'        | TO_DATE('16-10-2025','DD-MM-YYYY')       | TO_DATE('16-10-2025','DD-MM-YYYY')       | 'PER2'    | 0               | 'TEAM1' |
      | 'SUP2'        | TO_DATE('16-10-2025','DD-MM-YYYY')       | TO_DATE('16-10-2025','DD-MM-YYYY')       | 'PER2'    | 1               | 'TEAM2' |
   END VALUES;

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
IS
   return_   VARCHAR2(2000);
   expected_ VARCHAR2(2000);
BEGIN
   FOR
      | expected_ | person_id_ | date_                                  | team_id_ |
      | ''        | 'PER5'     | TO_DATE('16-10-2025','DD-MM-YYYY')     | NULL     | -- Not Team Setup
      | 'SUP1'    | 'PER1'     | TO_DATE('16-10-2025','DD-MM-YYYY')     | NULL     | -- Without Team ID
      | 'SUP1'    | 'PER1'     | TO_DATE('16-10-2025','DD-MM-YYYY')     | 'TEAM1'  | -- With Team ID
      | NULL      | 'PER1'     | TO_DATE('16-10-2025','DD-MM-YYYY')     | 'TEAM2'  | -- Different Team ID
   LOOP
      return_ := Get_Primary_Manager(person_id_, date_, team_id_);
      IF expected_ IS NULL AND return_ IS NULL THEN
         ASSERT TRUE;
      ELSE
         ASSERT return_ = expected_ MESSAGE 'Expected '||expected_||' but returned '||return_;
      END IF;
   END LOOP;
END UNITTEST;
```

Key: Combines @MockTable for data + @MockPackage for external API. Test rows have trailing comments.

## Example 5: Procedure Test with Error Validation

Source: `BankDetails.pltst`

```sql
UNITTEST "Validate_Bank_Bic_Code should give an error when BIC code does not comply" FOR
   PROCEDURE Validate_Bank_Bic_Code (
      bic_code_ IN     VARCHAR2);
USING
   @MockPackage ERROR_SYS
   PROCEDURE Record_General (
      lu_name_  IN     VARCHAR2,
      err_text_ IN     VARCHAR2,
      p1_       IN     VARCHAR2 DEFAULT NULL,
      p2_       IN     VARCHAR2 DEFAULT NULL,
      p3_       IN     VARCHAR2 DEFAULT NULL )
   IS
      expected_  VARCHAR2(1000) := 'BICCODE: The BIC code :P1 must be 8 or 11 characters.';
      expected2_ VARCHAR2(1000) := 'BICCOUNTYCODE: Position 5 and 6 of the BIC :P1 should contain a valid Country Code.';
   BEGIN
      IF (err_text_ = expected_) THEN
         ASSERT err_text_ = expected_ MESSAGE 'Expected '|| expected_ ||' but returned '|| err_text_;
      ELSIF (err_text_ = expected2_) THEN
         ASSERT err_text_ = expected2_ MESSAGE 'Expected '|| expected2_ ||' but returned '|| err_text_;
      ELSE
         ASSERT err_text_ = expected_ MESSAGE 'Unexpected error text returned '|| err_text_;
      END IF;
   END Record_General;
IS
BEGIN
   FOR
      | bic_code_      |
      | 'AAAA'         | -- Too short
      | 'AAAABBCCDDDE' | -- Too long
      | NULL            |
      | ''              |
   LOOP
      Validate_Bank_Bic_Code(bic_code_);
   END LOOP;
END UNITTEST;
```

Key: Mock `ERROR_SYS.Record_General` and assert the error message inside the mock body.

## Example 6: @Mock for Local Functions

Source: `AccessSetupConfiguration.pltst`

```sql
   @Mock
   FUNCTION Get_Duration (
      company_id_ IN     VARCHAR2) RETURN NUMBER
   IS
   BEGIN
      RETURN duration_;
   END Get_Duration;

   @Mock
   FUNCTION Get_Duration_Unit_Db (
      company_id_ IN     VARCHAR2) RETURN VARCHAR2
   IS
   BEGIN
      RETURN duration_unit_;
   END Get_Duration_Unit_Db;
```

Key: `@Mock` (not `@MockPackage`) for functions in the same LU. Returns test variables set per loop iteration.

## Data Type Handling

| Type | In @MockTable / FOR data | In @Mock bodies |
|------|--------------------------|-----------------|
| VARCHAR2 | `'value'` | `'value'` |
| NUMBER | `1`, `0` (no quotes) | `1`, `0` |
| DATE | `TO_DATE('01/01/2024', 'dd/mm/yyyy')` | `TO_DATE(...)`, `SYSDATE` |
| BOOLEAN | `TRUE`/`FALSE` (no quotes) in FOR; `1`/`0` (NUMBER) in _tab | `TRUE`/`FALSE` |
| NULL | `NULL` keyword | `NULL` |

## Assertion Patterns

### Simple equality
```sql
ASSERT return_ = expected_ MESSAGE 'Expected '||expected_||' but returned '||return_;
```

### NULL-aware (recommended for any nullable return)
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
