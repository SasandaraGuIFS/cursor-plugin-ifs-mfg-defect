# IFS PL/SQL CRUD Lifecycle — Detailed Reference

## Insert Flow

The full call chain when a record is created:

```
Prepare_Insert___  →  Unpack___  →  Check_Insert___  →  Insert___
                                        ↓
                                  Check_Common___
```

### Prepare_Insert___

Sets default values before the record is unpacked. Works with the `attr_` string. This method is triggered when a user clicks the **plus (+) icon** on the client side to create a new record. The defaults populated here are what the user sees in the form before they start editing.

**Defect investigation tip**: If a user reports incorrect default column values when creating a new record (wrong dates, missing IDs, unexpected field values on the new record form), the issue almost always lies in `Prepare_Insert___`.

```sql
@Override
PROCEDURE Prepare_Insert___ (
   attr_ IN OUT VARCHAR2 )
IS
   temp_  NUMBER;
BEGIN
   super(attr_);
   SELECT EMP_PAYMENT_ID.NEXTVAL INTO temp_ FROM dual;
   Client_SYS.Add_To_Attr('PAYMENT_ID', temp_, attr_);
   Client_SYS.Add_To_Attr('CREATED_AT', SYSDATE, attr_);
   Client_SYS.Add_To_Attr('PAYMENT_DATE', SYSDATE, attr_);
END Prepare_Insert___;
```

Common defaults set here: sequence-generated IDs, SYSDATE timestamps, boolean defaults, default status values.

### Check_Common___

Runs for **both** inserts and updates. Validates business rules that apply regardless of operation. Called by Check_Insert___ and Check_Update___ via `super()`.

Parameters: `oldrec_` (empty on insert), `newrec_` (IN OUT), `indrec_` (indicator record — which fields changed), `attr_`.

```sql
@Override
PROCEDURE Check_Common___ (
   oldrec_ IN     invoice_series_tab%ROWTYPE,
   newrec_ IN OUT invoice_series_tab%ROWTYPE,
   indrec_ IN OUT Indicator_Rec,
   attr_   IN OUT VARCHAR2 )
IS
BEGIN
   super(oldrec_, newrec_, indrec_, attr_);
   -- Validate foreign key references
   IF (newrec_.way_id IS NOT NULL) THEN
      $IF Component_Payled_SYS.INSTALLED $THEN
         Payment_Way_API.Exist(newrec_.company, newrec_.way_id);
      $ELSE
         NULL;
      $END
   END IF;
   -- Validate value ranges
   IF (NVL(newrec_.max_no_char_for_pay_ref, 0) > 50) THEN
      Error_SYS.Appl_General(lu_name_, 'VALTOOLONG: Value of Max no. of char. for Payment Reference can not be greater than 50.');
   END IF;
   -- Validate conditional requirements
   IF (NVL(newrec_.tax_invoice, 'FALSE') = 'TRUE') THEN
      IF (NVL(Company_Tax_Control_Invoic_API.Get_Use_Tax_Invoice_Db(newrec_.company), 'FALSE') = 'FALSE') THEN
         Error_SYS.Appl_General(lu_name_, 'NOUSETAXINV1: Tax Invoice can only be selected if Use Tax Invoice is selected for the company.');
      END IF;
   END IF;
END Check_Common___;
```

### Check_Insert___

Validates rules specific to insertion. Always calls `super()` which invokes Check_Common___.

```sql
@Override
PROCEDURE Check_Insert___ (
   newrec_ IN OUT emp_payment_tab%ROWTYPE,
   indrec_ IN OUT Indicator_Rec,
   attr_   IN OUT VARCHAR2 )
IS
   name_  VARCHAR2(30);
   value_ VARCHAR2(4000);
   emp_for_ VARCHAR2(20);

   CURSOR pf IS
      SELECT format_id
      FROM emp_payment_method_tab
      WHERE company_id = newrec_.company_id
      AND method_id = newrec_.method_id
      AND valid_from <= trunc(sysdate)
      AND valid_to >= trunc(sysdate);
BEGIN
   super(newrec_, indrec_, attr_);   -- calls Check_Common___

   OPEN pf;
   FETCH pf INTO emp_for_;
   CLOSE pf;
   IF (emp_for_ != 'GER') THEN
      Error_SYS.Check_Not_Null(lu_name_, 'PAYMENT_DATE', newrec_.payment_date);
   END IF;
EXCEPTION
   WHEN value_error THEN
      Error_SYS.Item_Format(lu_name_, name_, value_);
END Check_Insert___;
```

### Check_Update___

Validates rules specific to updates. Receives `oldrec_` (previous state) and `newrec_` (new state).

```sql
@Override
PROCEDURE Check_Update___ (
   oldrec_ IN     emp_payment_tab%ROWTYPE,
   newrec_ IN OUT emp_payment_tab%ROWTYPE,
   indrec_ IN OUT Indicator_Rec,
   attr_   IN OUT VARCHAR2 )
IS
BEGIN
   super(oldrec_, newrec_, indrec_, attr_);   -- calls Check_Common___
   -- Update-specific validations comparing oldrec_ vs newrec_
EXCEPTION
   WHEN value_error THEN
      Error_SYS.Item_Format(lu_name_, name_, value_);
END Check_Update___;
```

### Check_Delete___

Validates that a record can be safely deleted. Checks for dependent records.

```sql
@Override
PROCEDURE Check_Delete___ (
   remrec_ IN invoice_series_tab%ROWTYPE )
IS
BEGIN
   $IF Component_Payled_SYS.INSTALLED $THEN
      Company_Pay_Info_API.Check_If_Default_Series(remrec_.company, remrec_.series_id);
   $END
   super(remrec_);
END Check_Delete___;
```

### Insert___

Core DML — inserts the record into the table. Called after all validation passes.

```sql
@Override
PROCEDURE Insert___ (
   objid_      OUT    VARCHAR2,
   objversion_ OUT    VARCHAR2,
   newrec_     IN OUT EMP_PAYMENT_TAB%ROWTYPE,
   attr_       IN OUT VARCHAR2 )
IS
BEGIN
   super(objid_, objversion_, newrec_, attr_);
   -- Post-insert logic (authorization checks, notifications, etc.)
   IF User_Access_API.Is_User_Company_Id(newrec_.company_id) IS NULL THEN
      Error_SYS.Record_General(lu_name_, 'NOAUTHCREATE: You are not authorized to create information in company :P1', newrec_.company_id);
   END IF;
EXCEPTION
   WHEN dup_val_on_index THEN
      Error_SYS.Record_Exist(lu_name_);
END Insert___;
```

### Update___

Core DML for updates. Receives both old and new record.

```sql
@Override
PROCEDURE Update___ (
   objid_      IN     VARCHAR2,
   oldrec_     IN     EMP_PAYMENT_TAB%ROWTYPE,
   newrec_     IN OUT EMP_PAYMENT_TAB%ROWTYPE,
   attr_       IN OUT VARCHAR2,
   objversion_ IN OUT VARCHAR2,
   by_keys_    IN     BOOLEAN DEFAULT FALSE )
IS
BEGIN
   -- Pre-update authorization
   IF User_Access_API.Is_User_Company_Id(newrec_.company_id) IS NULL THEN
      Error_SYS.Record_General(lu_name_, 'NOAUTHMODIFY: You are not authorized to modify information in company :P1', newrec_.company_id);
   END IF;
   super(objid_, oldrec_, newrec_, attr_, objversion_, by_keys_);
EXCEPTION
   WHEN dup_val_on_index THEN
      Error_SYS.Record_Exist(lu_name_);
END Update___;
```

## Update Flow (Programmatic — Lock, Modify, Save)

When modifying a record programmatically (not from UI):

```sql
PROCEDURE Set_Approved_Date___ (
   rec_  IN OUT CAMPAIGN_TAB%ROWTYPE,
   attr_ IN OUT VARCHAR2 )
IS
   oldrec_          CAMPAIGN_TAB%ROWTYPE;
   newrec_          CAMPAIGN_TAB%ROWTYPE;
   temp_attr_       VARCHAR2(50);
   temp_objversion_ VARCHAR2(20);
BEGIN
   -- 1. Lock the record
   oldrec_ := Lock_By_Keys___(rec_.campaign_id);
   -- 2. Copy old to new
   newrec_ := oldrec_;
   -- 3. Set new values via attr_ string
   Client_SYS.Add_To_Attr('APPROVED_DATE', rec_.approved_date, temp_attr_);
   -- 4. Unpack attr_ into newrec_
   Unpack___(newrec_, indrec_, temp_attr_);
   -- 5. Validate
   Check_Update___(oldrec_, newrec_, indrec_, temp_attr_);
   -- 6. Save
   Update___(NULL, oldrec_, newrec_, temp_attr_, temp_objversion_, TRUE);
END Set_Approved_Date___;
```

## Public CRUD Wrapper Pattern

Public API methods wrap the internal flow:

```sql
PROCEDURE New_Payment (
   tattr_ IN VARCHAR2 )
IS
   newrec_     EMP_PAYMENT_TAB%ROWTYPE;
   indrec_     Indicator_Rec;
   objid_      EMP_PAYMENT.objid%TYPE;
   objversion_ EMP_PAYMENT.objversion%TYPE;
   attr_       VARCHAR2(2000);
BEGIN
   attr_ := tattr_;
   Unpack___(newrec_, indrec_, attr_);
   Check_Insert___(newrec_, indrec_, attr_);
   Insert___(objid_, objversion_, newrec_, attr_);
END New_Payment;
```

## Record Type Conventions

| Variable | Type | Used in |
|----------|------|---------|
| `newrec_` | `<table>_tab%ROWTYPE` | Insert/Update — the new record state |
| `oldrec_` | `<table>_tab%ROWTYPE` | Update — the old record state (before change) |
| `remrec_` | `<table>_tab%ROWTYPE` | Delete — the record being removed |
| `indrec_` | `Indicator_Rec` | Tracks which fields were modified |
| `attr_` | `VARCHAR2` | Packed attribute string — carries field values between layers |
| `objid_` | `VARCHAR2` | Object ID (ROWID) |
| `objversion_` | `VARCHAR2` | Optimistic locking version (timestamp) |

## Exist / Check_Exist Pattern

```sql
-- Raises error if not found
@Override
@UncheckedAccess
PROCEDURE Exist (
   payment_id_ IN NUMBER )
IS
BEGIN
   super(payment_id_);
   -- Additional authorization checks
END Exist;

-- Returns 'TRUE'/'FALSE'
@UncheckedAccess
FUNCTION Check_Exist (
   company_   IN VARCHAR2,
   series_id_ IN VARCHAR2 ) RETURN VARCHAR2
IS
   dummy_ NUMBER;
   CURSOR exist IS
      SELECT 1
      FROM invoice_series_tab
      WHERE company = company_
      AND series_id = series_id_;
BEGIN
   OPEN exist;
   FETCH exist INTO dummy_;
   IF (exist%FOUND) THEN
      CLOSE exist;
      RETURN 'TRUE';
   ELSE
      CLOSE exist;
      RETURN 'FALSE';
   END IF;
END Check_Exist;
```
