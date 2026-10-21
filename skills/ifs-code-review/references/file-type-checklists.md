# IFS Code Review Checklists by File Type

Sourced from the [SC Code Review Checklist](https://ifsdev.atlassian.net/wiki/spaces/SC/pages/1097629802) and the SE Code Review Checklist spreadsheet.

## Entity (.entity)

- Verify entity name is meaningful and follows length standard
- Check correct composite key and parent keys
- Check public/private attributes are properly added
- Check proper field types and sizes
- Check proper attribute flags
- Check required CodeGen properties
- Check proper row level security is added
- Check entity labels are self-explanatory
- Cross-check associated keys' data type and length with parent/reference entities
- Verify Model Tester runs without errors
- When converting Derived to Ordinary attribute, test all dependent functional flows

## PL/SQL (.plsql)

### Basic
- Static Code Analyzer runs without errors; warnings analyzed
- Developer Studio warnings analyzed and handled
- No API-breaking changes through support; whitelist if unavoidable
- Newly added methods are unit-testable; unit test or `@IgnoreUnitTest` annotation added
- No duplicated messages
- No enumeration client values reaching server code
- No hard-coded values; use constants or enumeration DB values
- Default values added when adding new parameters to existing methods
- Parameter order: OUT first, then IN OUT, then IN
- Avoid removing or renaming PL/SQL methods and parameters
- Avoid changing parameter data types
- Use column type (`%TYPE`) and row type (`%ROWTYPE`) in variable declarations
- Initialize variables at declaration when possible
- Lowercase table/view names in cursors
- Do not add API calls inside cursors
- Use generated framework methods (rec-based) for CUD actions, not attribute strings
- No direct table INSERT/UPDATE/DELETE — use framework CRUD methods
- Close all cursors after use

### Extended
- Check for duplicated code; create reusable methods
- No potential security vulnerabilities
- No performance bottlenecks; SQL/PL/SQL best practices followed
- Proper exception handling
- No multiple server calls for the same value
- Use DB values instead of client values
- Use bind variables instead of concatenation (prevent SQL injection)
- COMMIT/ROLLBACK/SAVEPOINT usage justified and documented

## PLSVC (.plsvc)

### Basic
- Developer Studio warnings analyzed
- Static Code Analyzer clean
- Check whether logic can be moved to `.plsql` level (plsvc is part of client layer)
- Correct LENGTH and DATATYPE declarations
- Better description in DESIGN HISTORY
- Convert to same case (UPPER/LOWER) for string comparisons
- Do not access tables or private views outside the component
- Use `IS NULL` for NULL comparisons
- Close cursors after use
- No duplicate error messages; consider moving to plsql
- No length value on NUMBER datatype
- Use DB values instead of client values

### Extended
- No API-breaking changes through support
- Special consideration when overriding/overtaking fragment plsvc implementations
- Check affected TAR scripts before merge
- Correct dynamic component dependencies
- Performance consideration
- Avoid SQL injection (use bind variables)
- Proper exception handling in plsvc or plsql
- Use framework-generated methods where possible

## Views (.views)

### Basic
- Static Code Analyzer clean; warnings analyzed
- Correct values in COLUMN DEFINITIONS section
- Correct stereotype (Private, Public, LOV) with proper suffix
- View column properties align with entity column properties (LENGTH, FORMAT, KEYS)
- Better description in DESIGN HISTORY
- Decide data source: TABLE vs VIEW and reason for VIEW usage
- Convert to same case for string comparisons
- Do not access tables or private views outside the component
- Use `IS NULL` for NULL comparisons
- No `&` sign usage inside comments

### Extended
- Valid reason to create new view instead of reusing existing
- Verify installation order/sequence across components
- Performance consideration
- Correct dynamic component dependency usage
- Check security check tags (`@SecurityCheck`)
- Language translation generated accordingly
- Use `ORDER BY` when order is needed
- UNION vs UNION ALL — UNION is costly

## Projection (.projection)

- Static Code Analyzer clean; warnings analyzed
- Projection name meaningful, follows naming/length standard (suffix: Handling, Analysis, etc.)
- Entity/query keys correctly set and matched with model entity
- No duplicated references; reference/referee keys correct
- No duplicated attributes; unnecessary overridden attributes removed
- Cross-check attribute properties (type, length, tags) with model entities
- Boolean attributes with fetch as API call have defaults via `CRUD_Default___`
- Overtaken attribute lengths specified and match entity; comment if different
- Dynamic dependencies correctly set
- Security: use bounded actions; proper initial check set
- Performance: avoid fetch attributes with Get methods when possible; avoid expensive ARRAY JOINs; avoid REFERENCE causing OUTER JOIN against complex LOV views

## Client (.client)

- Static Code Analyzer clean
- Client name meaningful and aligned with projection name
- Page has proper label; navigator entry set correctly
- Dynamic dependencies correctly set for dynamic elements
- Server calls optimized (bundle when possible)
- Reference attributes considered

## CDB/UPG (.cdb, .upg)

- CDB file is redeployable
- Naming standard followed for development and support
- Cross-check index definitions between CDB and storage file
- Code blocks in correct sections
- Timestamps and prompts correct
- DML operations followed by COMMIT
- No interaction with dynamic components; no DML with static components; no conditional compilation
- Support CDB files contain only `Database_SYS` calls
- Upgrade version correctly defined
- Efficient code for large data volumes

## Storage (.storage)

- Indexes, temporary tables, and sequences in proper format
- On EBR tracks (25R2+): indexes reference `_rtb`, not `_tab`

## PLTST (.pltst)

- Unit test provides genuine value (understand benefit of this test)
- `@IgnoreUnitTest` added to plsql methods where unit test is unnecessary
- Tests **behavior**, not technical implementation
- All behaviors and input/output combinations tested, including NULL values
- Meaningful test name describing the scenario
- Row numbers added for test scenarios (good practice)
- Meaningful comments for mock table lines
- Code properly aligned
- Use CONSTANT for SYSDATE; don't call SYSDATE repeatedly
- Remove framework comment blocks
- ASSERT aligned with what's being tested

## Script-A REST Tests (.mkd)

### Design
- Test objective clear; prerequisite data carefully designed
- Happy path always included
- Positive and negative paths covered (use expect failure)
- No duplicate test cases; maximize coverage within single test
- Prefer extending existing tests over adding new ones

### Naming & Structure
- Correct folder aligned with Process Diagram
- Meaningful script names; correct spelling
- PascalCase for keywords/script names; camelCase for variables

### Code Quality
- No unused variables or input parameters
- No unnecessary comments (prefer good naming)
- No `Delay` with fixed time span (use helpers)
- No `Print` commands in merged code
- Use `Create`, `Modify`, `Action` instead of `Post`, `Patch`
- GET requests fetch only required attributes
- Arrays accessed with consistent ordering (`Order By`)

### Rerunnability
- Test is rerunnable and parallel-safe
- Random values for keys/unique fields
- Standalone tests have no dependencies on other tests

### Assertions
- AAA structure (Arrange/Act/Assert) descriptions match actual test behavior
- Util scripts are reusable and must NOT contain Asserts
- Output statement present when script description says it returns a value

### Performance
- Minimize setup/teardown operations
- Connect to user once at start; minimize user switching
- Reuse test data within scripts instead of recreating
- Balance coverage with execution time

## General (All Files)

- Solution properly implements the defect fix or development requirement
- Spellings correct in file names, variable names, programming constructs
- File names are self-descriptive
- History comments added (YYMMDD Sign Ticket format)
- Bug tags present on support tracks (not needed on master)
- EBR compliance on 25R2+ tracks
- Automated tests updated and passing
- Cross-product corrections have two code reviewers
