---
name: ifs-plsql-patterns
description: This skill should be used when reading, writing, or modifying IFS Cloud PL/SQL code (.plsql, .plsvc files), investigating CRUD lifecycle bugs, understanding Check_Common___, Check_Insert___, Prepare_Insert___ patterns, working with Error_SYS error handling, Client_SYS attribute strings, projection service overrides (CRUD_Create___, CRUD_Update___), or tracing business logic through the IFS architecture layers.
---

# IFS PL/SQL Patterns

This skill provides the coding conventions, patterns, and framework APIs used in IFS Cloud PL/SQL development. Use it when reading, modifying, or writing `.plsql` and `.plsvc` files.

## PLSQL File Structure

IFS `.plsql` files follow a standard section layout:

```
Header (history comments, component info)
layer Core;

-------------------- PUBLIC DECLARATIONS ------------------------------------
-------------------- PRIVATE DECLARATIONS -----------------------------------
-------------------- LU SPECIFIC IMPLEMENTATION METHODS ---------------------
  (Check_Common___, Check_Insert___, Check_Update___, Check_Delete___)
  (Prepare_Insert___, Insert___, Update___, Delete___)
  (Private helper methods)
-------------------- LU SPECIFIC PRIVATE METHODS ----------------------------
  (New__, Modify__, Remove__ wrappers)
-------------------- LU SPECIFIC PROTECTED METHODS --------------------------
-------------------- LU SPECIFIC PUBLIC METHODS -----------------------------
  (Get_*, Create_*, Modify_*, Remove_*, Exist, Check_Exist)
```

## CRUD Lifecycle

### Insert Flow

```
User clicks (+) → Prepare_Insert___ → UI form shown with defaults
User saves      → Unpack___ → Check_Insert___ → Insert___
                                    ↓
                              Check_Common___
```

### Update Flow

```
User saves changes → Unpack___ → Check_Update___ → Update___
                                       ↓
                                 Check_Common___
```

### Programmatic Update Flow (Lock-Modify-Save)

```sql
oldrec_ := Lock_By_Keys___(key_);
newrec_ := oldrec_;
-- Set new values via attr_
Unpack___(newrec_, indrec_, attr_);
Check_Update___(oldrec_, newrec_, indrec_, attr_);
Update___(NULL, oldrec_, newrec_, attr_, objversion_, TRUE);
```

## Key Method Signatures

| Method | Purpose | Key parameters |
|--------|---------|---------------|
| `Prepare_Insert___` | Set defaults for new record (triggered by + button) | `attr_ IN OUT` |
| `Check_Common___` | Validate on both insert and update | `oldrec_`, `newrec_`, `indrec_`, `attr_` |
| `Check_Insert___` | Insert-specific validation (calls `super` → Check_Common___) | `newrec_`, `indrec_`, `attr_` |
| `Check_Update___` | Update-specific validation (calls `super` → Check_Common___) | `oldrec_`, `newrec_`, `indrec_`, `attr_` |
| `Check_Delete___` | Delete validation (check for dependents) | `remrec_` |
| `Insert___` | Core DML insert | `objid_`, `objversion_`, `newrec_`, `attr_` |
| `Update___` | Core DML update | `objid_`, `oldrec_`, `newrec_`, `attr_`, `objversion_`, `by_keys_` |

All `@Override` methods must call `super()` to invoke the framework-generated base logic.

## Record Variable Naming

| Variable | Type | Meaning |
|----------|------|---------|
| `newrec_` | `<table>_tab%ROWTYPE` | New/modified record state |
| `oldrec_` | `<table>_tab%ROWTYPE` | Previous record state (before update) |
| `remrec_` | `<table>_tab%ROWTYPE` | Record being deleted |
| `indrec_` | `Indicator_Rec` | Which fields were changed |
| `attr_` | `VARCHAR2` | Packed attribute string carrying field values |

## Client_SYS Attribute Strings

The `attr_` string passes field values between layers using `Client_SYS`:

```sql
Client_SYS.Clear_Attr(attr_);
Client_SYS.Add_To_Attr('COLUMN_NAME', value_, attr_);
value_ := Client_SYS.Get_Item_Value('COLUMN_NAME', attr_);
```

**Attribute naming**: Names are UPPER_CASE matching the entity column. For enumeration (IID) columns, append `_DB` to pass the raw database value:

```sql
Client_SYS.Add_To_Attr('PARTY_TYPE_DB', 'CUSTOMER', attr_);  -- DB value
Client_SYS.Add_To_Attr('PARTY_TYPE', display_value_, attr_);  -- client value (requires decode)
```

## Error Handling

| Method | When to use |
|--------|------------|
| `Error_SYS.Appl_General(lu_name_, 'TAG: Message :P1', param_)` | General business rule violation |
| `Error_SYS.Record_General(lu_name_, 'TAG: Message :P1', param_)` | Record-level error |
| `Error_SYS.Check_Not_Null(lu_name_, 'FIELD', value_)` | Required field is NULL |
| `Error_SYS.Record_Exist(lu_name_)` | Duplicate record (in `WHEN dup_val_on_index`) |
| `Error_SYS.Record_Not_Exist(lu_name_)` | Referenced record not found |
| `Error_SYS.Item_Format(lu_name_, name_, value_)` | Field format error (in `WHEN value_error`) |

## PLSVC (Projection Service) Layer

`.plsvc` files override framework CRUD for the UI projection:

| Method | Purpose |
|--------|---------|
| `CRUD_Default___` | Provide defaults for new UI record (complements `Prepare_Insert___`) |
| `CRUD_Default_Copy___` | Reset fields when copying a record |
| `CRUD_Create___` | Pre/post-process record creation from UI |
| `CRUD_Update___` | Pre/post-process record update from UI |
| `CRUD_Delete___` | Pre/post-process record deletion from UI |

Action methods implement custom operations invoked by client commands.

The call chain: `CRUD_Create___ (plsvc) → super() → Prepare_Insert___ → Check_Insert___ → Check_Common___ → Insert___ (all in plsql)`.

## Dynamic Component Dependencies

**Compile-time** (`$IF`):
```sql
$IF Component_Payled_SYS.INSTALLED $THEN
   Payment_Way_API.Exist(newrec_.company, newrec_.way_id);
$ELSE
   NULL;
$END
```

**Runtime**:
```sql
IF (Dictionary_SYS.Component_Is_Installed('EMPPAY')) THEN ...
```

**Annotation** (space-separated, no brackets):
```sql
@DynamicComponentDependency ORDER
PROCEDURE Some_Method___ (...)
```

## Common Annotations

| Annotation | Purpose |
|------------|---------|
| `@Override` | Overrides framework method — must call `super()` |
| `@UncheckedAccess` | Bypasses authorization (read-only getters) |
| `@IgnoreUnitTest` | Exempts from test requirement (needs reason) |
| `@ApproveTransactionStatement` | Required before explicit `COMMIT`/`ROLLBACK` |
| `@DynamicComponentDependency COMP` | Marks dependency on optional component |

## Table Access

PL/SQL accesses base tables directly with the `_tab` suffix. Views (without `_tab`) are used by the projection/UI layer.

```sql
SELECT company_id FROM emp_payment_tab WHERE ...    -- direct table (in .plsql)
SELECT company_id FROM emp_payment WHERE ...         -- view (in projection/UI)
```

## Defect Investigation Quick Guide

| Symptom | Where to look |
|---------|--------------|
| Wrong defaults on new record form | `Prepare_Insert___` (.plsql), then `CRUD_Default___` (.plsvc) |
| Validation error on save (insert) | `Check_Insert___` → `Check_Common___` |
| Validation error on save (update) | `Check_Update___` → `Check_Common___` |
| Wrong enum value / "value not found" on IID | Check `_DB` suffix in `Client_SYS.Add_To_Attr` calls |
| Authorization / "not authorized" error | `User_Access_API` checks in `Insert___` / `Update___` |
| Duplicate record error | `EXCEPTION WHEN dup_val_on_index` in `Insert___` / `Update___` |
| Cross-component call failure | `$IF Component_*_SYS.INSTALLED` or `Dictionary_SYS.Component_Is_Installed` guards |
| State transition rejected | State machine in `.entity`, guard methods in `.plsql` |
| Copied record has wrong values | `CRUD_Default_Copy___` in `.plsvc` |

## Additional Resources

### Reference Files

For detailed code examples and full method signatures:
- **`references/crud-lifecycle.md`** — Complete CRUD lifecycle with real code examples: Prepare_Insert___, Check_Common___, Check_Insert___, Check_Update___, Check_Delete___, Insert___, Update___, programmatic update flow, Exist/Check_Exist patterns
- **`references/plsvc-patterns.md`** — Projection service patterns: CRUD_Create___, CRUD_Update___, CRUD_Default___, CRUD_Default_Copy___, action methods, function methods returning structures, call chain from plsvc to plsql
- **`references/error-and-framework-apis.md`** — Error_SYS methods, exception handling, Client_SYS attribute strings with naming conventions, annotations, dynamic dependencies, security APIs, logging, autonomous transactions, table access, custom record types
