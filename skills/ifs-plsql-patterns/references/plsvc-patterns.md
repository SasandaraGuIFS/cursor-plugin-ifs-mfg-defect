# IFS PLSVC (Projection Service) Patterns — Detailed Reference

`.plsvc` files implement the server-side logic for Aurena UI projections. They override framework CRUD methods and define custom actions.

## CRUD_Create___ Override

Intercepts record creation from the UI. Allows pre-processing, custom validation, or transformation before the record is saved.

```sql
@Override
PROCEDURE CRUD_Create___ (
   etag_   IN OUT VARCHAR2,
   key_    IN OUT Invoice_Series_Key,
   attr_   IN OUT VARCHAR2,
   info_   OUT    VARCHAR2,
   action_ IN     VARCHAR2 )
IS
   rec_  Invoice_Series_Rec;
BEGIN
   Add_To_Rec_From_Attr___(attr_, rec_);
   Common_Validations___(rec_.company, rec_.series_id, rec_);
   super(etag_, key_, attr_, info_, action_);
END CRUD_Create___;
```

Key points:
- `key_` is a typed record matching the entity's primary key
- `attr_` carries field values as a packed string
- `action_` is typically `'DO'` (execute) or `'CHECK'` (validate only)
- `Add_To_Rec_From_Attr___` unpacks attr_ into a typed record for easier access
- Always call `super()` to execute the actual insert

## CRUD_Update___ Override

Intercepts record updates from the UI.

```sql
@Override
PROCEDURE CRUD_Update___ (
   etag_   IN OUT VARCHAR2,
   key_    IN OUT Invoice_Series_Key,
   attr_   IN OUT VARCHAR2,
   info_   OUT    VARCHAR2,
   action_ IN     VARCHAR2 )
IS
   rec_  Invoice_Series_Rec;
BEGIN
   Add_To_Rec_From_Attr___(attr_, rec_);
   Common_Validations___(key_.company, key_.series_id, rec_);
   super(etag_, key_, attr_, info_, action_);
END CRUD_Update___;
```

## CRUD_Delete___ Override

Intercepts record deletion from the UI.

```sql
@Override
PROCEDURE CRUD_Delete___ (
   etag_   IN OUT VARCHAR2,
   key_    IN OUT Some_Entity_Key,
   info_   OUT    VARCHAR2,
   action_ IN     VARCHAR2 )
IS
BEGIN
   -- Pre-delete logic
   super(etag_, key_, info_, action_);
END CRUD_Delete___;
```

## CRUD_Default___ Override

Provides default values when the UI creates a new record. This is the projection-layer equivalent of `Prepare_Insert___` in `.plsql`. Triggered when the user clicks the plus (+) icon in the UI.

**Defect investigation tip**: If default values are wrong on a new record form and `Prepare_Insert___` looks correct, check `CRUD_Default___` in the `.plsvc` — it can override or supplement the defaults.

```sql
@Override
PROCEDURE CRUD_Default___(
   key_  IN  Emp_Payment_Trans_Key,
   attr_ IN  OUT VARCHAR2,
   info_ OUT VARCHAR2)
IS
   company_id_ VARCHAR2(100);
BEGIN
   company_id_ := Client_SYS.Get_Item_Value('COMPANY_ID', attr_);
   IF company_id_ IS NULL THEN
      company_id_ := User_Access_API.Get_User_Default_Company_Id();
   END IF;
   Client_SYS.Add_To_Attr('COMPANY_ID', company_id_, attr_);
   -- ... more defaults ...
   super(key_, attr_, info_);
END CRUD_Default___;
```

## CRUD_Default_Copy___ Override

Called when a user copies an existing record. Resets fields that should not be duplicated (IDs, timestamps, statuses).

```sql
@Override
PROCEDURE CRUD_Default_Copy___ (
   rec_  IN OUT Emp_Payment_Trans_Rec )
IS
BEGIN
   IF rec_.company_id IS NULL THEN
      rec_.company_id := User_Access_API.Get_User_Default_Company_Id();
   END IF;
   rec_.expense_id := NULL;          -- Reset generated ID
   rec_.dom_amount := NULL;          -- Reset calculated fields
   rec_.payment_id := NULL;
   rec_.authorized_by := NULL;       -- Reset approval
   rec_.authorized_at := NULL;
   rec_.created_by := FND_SESSION_API.Get_Fnd_User;
   rec_.created_at := SYSDATE;
   rec_.emp_payment_status := 'R';   -- Reset to initial status
   super(rec_);
END CRUD_Default_Copy___;
```

## Action Methods

Custom business operations invoked from client commands. These are defined in the `.projection` file as `action` and implemented in the `.plsvc`.

```sql
-- Simple action delegating to the entity API
PROCEDURE Do_Authorize_Payment___(
   key_ IN Emp_Payment_Trans_Key)
IS
BEGIN
   Emp_Payment_Trans_API.Authorize_Payments(key_.emp_pay_trans_id);
END Do_Authorize_Payment___;
```

## Function Methods Returning Structures

Functions that return typed records (structures defined in the `.projection`) to the UI.

```sql
FUNCTION Get_Defaults___(
   company_id_ IN VARCHAR2,
   expense_id_ IN NUMBER) RETURN Struct_Emp_Transaction_Rec
IS
   rec_ Struct_Emp_Transaction_Rec;
BEGIN
   Emp_Payment_Trans_API.Get_Defaults(
      rec_.curr_rate, rec_.curr_amount, rec_.method_id,
      rec_.account, rec_.emp_no, rec_.curr_code,
      company_id_, expense_id_);
   RETURN rec_;
END Get_Defaults___;
```

## How PLSVC Calls PLSQL

The `.plsvc` layer delegates business logic to `.plsql` API methods:

```
CRUD_Create___ (plsvc)
  → super() → framework calls:
    → Prepare_Insert___ (plsql)
    → Check_Insert___ (plsql) → Check_Common___ (plsql)
    → Insert___ (plsql)
```

The `.plsvc` adds projection-specific logic (UI defaults, attribute transformation) while `.plsql` contains the core business rules.

## Common Pattern: Shared Validation in PLSVC

```sql
-- Private validation method shared by CRUD_Create___ and CRUD_Update___
PROCEDURE Common_Validations___ (
   company_   IN VARCHAR2,
   series_id_ IN VARCHAR2,
   rec_       IN Invoice_Series_Rec )
IS
BEGIN
   -- Projection-layer validations
END Common_Validations___;
```
