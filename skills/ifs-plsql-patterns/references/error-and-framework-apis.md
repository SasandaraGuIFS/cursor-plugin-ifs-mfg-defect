# IFS Error Handling & Framework APIs — Detailed Reference

## Error_SYS Methods

### Error_SYS.Appl_General — General application error (most common)

Format: `Error_SYS.Appl_General(lu_name_, 'TAG: Message text :P1 :P2', param1_, param2_);`

- The tag before the colon (e.g. `VALTOOLONG`) is a unique identifier for the error
- `:P1`, `:P2`, etc. are parameter placeholders substituted at runtime
- `lu_name_` is the logical unit name constant (defined in the package)

```sql
Error_SYS.Appl_General(lu_name_, 'VALTOOLONG: Value of Max no. of char. for Payment Reference can not be greater than 50.');

Error_SYS.Appl_General(lu_name_, 'NOUSETAXINV1: Tax Invoice can only be selected if Use Tax Invoice is selected for the company.');

Error_SYS.Appl_General(lu_name_, 'INVALIDREFSITE: Reference site :P1 is not connected to Company :P2.', reference_site_, company_);
```

### Error_SYS.Record_General — Generic record-level error

Same format as Appl_General but semantically tied to a specific record operation.

```sql
Error_SYS.Record_General(lu_name_, 'NOAUTHCREATE: You are not authorized to create information in company :P1', newrec_.company_id);

Error_SYS.Record_General(lu_name_, 'DEALNOTVALID: Deal(s) :P1 must have one of price including tax...', deal_ids_);
```

### Error_SYS.Check_Not_Null — Required field validation

Raises an error if the value is NULL. Generates a standard "Field X must have a value" message.

```sql
Error_SYS.Check_Not_Null(lu_name_, 'PAYMENT_DATE', newrec_.payment_date);
```

### Error_SYS.Record_Exist — Duplicate record

Used in EXCEPTION blocks when `dup_val_on_index` is caught.

```sql
EXCEPTION
   WHEN dup_val_on_index THEN
      Error_SYS.Record_Exist(lu_name_);
```

### Error_SYS.Record_Not_Exist — Record not found

Used when a referenced record doesn't exist.

```sql
Error_SYS.Record_Not_Exist(lu_name_);
```

### Error_SYS.Item_Format — Field format error

Used when a field value has an invalid format.

```sql
EXCEPTION
   WHEN value_error THEN
      Error_SYS.Item_Format(lu_name_, name_, value_);
```

### Error_SYS.Strip_Ora_Error — Clean Oracle error messages

Strips the ORA- prefix from Oracle error messages for cleaner logging.

```sql
Error_SYS.Strip_Ora_Error(sqlerrm)
```

## Standard Exception Handling Pattern

```sql
EXCEPTION
   WHEN dup_val_on_index THEN
      Error_SYS.Record_Exist(lu_name_);
   WHEN no_data_found THEN
      RETURN NULL;
   WHEN too_many_rows THEN
      Raise_Too_Many_Rows___(key_field_, 'Method_Name');
   WHEN value_error THEN
      Error_SYS.Item_Format(lu_name_, name_, value_);
   WHEN OTHERS THEN
      -- Log and re-raise
      RAISE;
END;
```

## Client_SYS Attribute String Pattern

The `attr_` string is a packed key-value format used to pass data between layers. It is the primary mechanism for transferring field values in IFS Cloud.

### Client_SYS.Clear_Attr — Reset the string

```sql
Client_SYS.Clear_Attr(attr_);
```

### Client_SYS.Add_To_Attr — Add a name/value pair

```sql
Client_SYS.Add_To_Attr('COMPANY_ID', company_id_, attr_);
Client_SYS.Add_To_Attr('PAYMENT_DATE', SYSDATE, attr_);
Client_SYS.Add_To_Attr('IS_ITEM_VISIBLE', 1, attr_);
```

### Client_SYS.Get_Item_Value — Read a value

```sql
company_id_ := Client_SYS.Get_Item_Value('COMPANY_ID', attr_);
```

### Full New Record Workflow Using attr_

```sql
Client_SYS.Clear_Attr(attr_);
Client_SYS.Add_To_Attr('COMPANY_ID', company_id_, attr_);
Client_SYS.Add_To_Attr('TEMPLATE_ID', template_id_, attr_);
Client_SYS.Add_To_Attr('DETAIL_ITEM', detail_item_, attr_);
New__(info_, objid_, objversion_, attr_, 'DO');
```

### Full Modify Record Workflow Using attr_

```sql
Client_SYS.Clear_Attr(attr_);
Client_SYS.Add_To_Attr('METHOD_ID', rec_.method_id, attr_);
Client_SYS.Add_To_Attr('ACCOUNT', rec_.account, attr_);
Emp_Payment_Trans_API.Modify_By_Keys(key_.emp_pay_trans_id, attr_);
```

### Attribute Naming Conventions

Attribute names in `Client_SYS.Add_To_Attr` must follow specific naming rules:

| Pattern | Meaning | Example |
|---------|---------|---------|
| `COLUMN_NAME` | Standard column — uses the entity/table column name in UPPER_CASE | `'COMPANY_ID'`, `'PAYMENT_DATE'`, `'TEMPLATE_ID'` |
| `COLUMN_NAME_DB` | Database value of an enumeration (IID) column — the internal stored value, not the client-facing display value | `'PARTY_TYPE_DB'`, `'SUPPLY_CODE_DB'`, `'INVOICE_METHOD_DB'` |

**Standard attributes**: The name matches the column name exactly as defined in the `.entity` file or `_tab` table, in UPPER_CASE with underscores.

```sql
Client_SYS.Add_To_Attr('COMPANY_ID', company_id_, attr_);
Client_SYS.Add_To_Attr('PAYMENT_DATE', SYSDATE, attr_);
Client_SYS.Add_To_Attr('TAX_INVOICE', 'FALSE', attr_);
```

**`_DB` suffix for enumerations**: When an attribute is an IID (enumeration) type, the `_DB` suffix passes the database-stored value directly (e.g., `'CUSTOMER'`, `'TRUE'`), bypassing client-side encoding/decoding. Without `_DB`, the framework expects the client-side display value which must be decoded.

```sql
-- Pass the DB-stored enum value directly
Client_SYS.Add_To_Attr('PARTY_TYPE_DB', 'CUSTOMER', attr_);
Client_SYS.Add_To_Attr('SUPPLY_CODE_DB', Cmpunt_Material_Req_Sup_API.DB_PROJECT_INVENTORY, attr_);
Client_SYS.Add_To_Attr('IS_ACTIVE_DB', is_active_db_, attr_);
```

**Defect investigation tip**: If an enumeration value is being set incorrectly or a "value not found" error occurs on an IID column, check whether the `_DB` suffix is present or missing. Using `PARTY_TYPE` without `_DB` expects a client-decoded value; using `PARTY_TYPE_DB` expects the raw database value.

## Annotation Patterns

### @Override

Marks a method as overriding its parent (framework-generated) implementation. Always call `super()` to invoke the base behavior.

```sql
@Override
PROCEDURE Check_Common___ (...)
IS
BEGIN
   super(oldrec_, newrec_, indrec_, attr_);
   -- Custom logic
END Check_Common___;
```

### @UncheckedAccess

Marks public methods that bypass authorization checks. Used for read-only getters and utility functions.

```sql
@UncheckedAccess
FUNCTION Get_Invoice_Type (
   company_   IN VARCHAR2,
   series_id_ IN VARCHAR2 ) RETURN VARCHAR2
```

### @IgnoreUnitTest

Exempts a method from unit test requirements. Must include a reason.

```sql
@IgnoreUnitTest TrivialFunction
FUNCTION Fetch_Series_Validation_Code (...)

@IgnoreUnitTest NoOutParams
PROCEDURE Insert_Detail_Item__ (...)
```

### @ApproveTransactionStatement

Required annotation before any explicit `COMMIT` or `ROLLBACK`. Includes date and developer sign for audit trail.

```sql
@ApproveTransactionStatement(2020-02-07,ovjose)
COMMIT;
```

### @DynamicComponentDependency

Marks methods or references that depend on optional (DYNAMIC) components. Uses a space separator, **no parentheses**.

```sql
@DynamicComponentDependency ORDER
PROCEDURE Some_Method___ (...)

@DynamicComponentDependency FNDADM
FUNCTION Get_Something (...)
```

## Dynamic Component Dependencies

### Conditional Compilation ($IF)

Compile-time guard for optional components. Code inside `$IF ... $END` is only compiled if the component is installed.

```sql
$IF Component_Payled_SYS.INSTALLED $THEN
   Payment_Way_API.Exist(newrec_.company, newrec_.way_id);
$ELSE
   NULL;
$END
```

### Runtime Check (Dictionary_SYS)

Runtime guard for optional components. Used when compile-time checking is not possible.

```sql
IF (Dictionary_SYS.Component_Is_Installed('EMPPAY')) THEN
   -- Safe to call Emppay APIs
END IF;
```

## Security/Authorization APIs

### User_Access_API

```sql
-- Check if user has access to a company
IF User_Access_API.Is_User_Company_Id(company_id_) IS NULL THEN
   Error_SYS.Record_General(lu_name_, 'NOAUTH: Not authorized for company :P1', company_id_);
END IF;

-- Get user's default company
company_id_ := User_Access_API.Get_User_Default_Company_Id();

-- Get person ID of current user
person_id_ := User_Access_API.Get_User_Current_Person_Id;
```

### FND_SESSION_API

```sql
-- Get current logged-in user
user_ := FND_SESSION_API.Get_Fnd_User;
```

## Logging/Tracing APIs

### Trace_SYS — Development tracing

```sql
Trace_SYS.Message('*********** Acknowledge_Payment********');
Trace_SYS.Message('company_id_       : ' || company_id_);
Trace_SYS.Message('payment_id_       : ' || payment_id_);
```

### Log_SYS — Application logging

```sql
IF (Log_SYS.Is_Log_Set(Log_Category_API.DB_ALL)) THEN
   Log_SYS.App_Trace(Log_SYS.trace_, '###Receive_Account###');
END IF;
```

## Autonomous Transactions

Used for operations that must commit independently (e.g., error logging).

```sql
PROCEDURE Write_Error_Msg___(
   message_type_ IN VARCHAR2,
   error_        IN VARCHAR2)
IS
   PRAGMA AUTONOMOUS_TRANSACTION;
BEGIN
   Fincon_Error_Msg_API.Write_Error(msg_id_, message_type_, error_);
   @ApproveTransactionStatement(2020-02-07,ovjose)
   COMMIT;
END Write_Error_Msg___;
```

## Table Access Pattern (_tab suffix)

PL/SQL code accesses base tables directly using the `_tab` suffix. Views (without `_tab`) are used by the UI layer.

```sql
-- Direct table access in PL/SQL
SELECT company_id FROM emp_payment_tab WHERE payment_id = payment_id_;

-- View access (used by projection/UI layer)
SELECT company_id FROM emp_payment WHERE payment_id = payment_id_;
```

## Custom Record Types

Defined in the PRIVATE DECLARATIONS section for complex operations.

```sql
TYPE EmpPaymentRec IS RECORD (
   company_id_save_    VARCHAR2(20),
   date_save_          DATE,
   curr_code_acc_      VARCHAR2(3),
   pay_curr_code_      VARCHAR2(3),
   pay_rate_           NUMBER
);

TYPE part_rec IS RECORD (
   catalog_no CAMPAIGN_PART_TAB.CATALOG_NO%TYPE
);
TYPE part_table IS TABLE OF part_rec;
```
