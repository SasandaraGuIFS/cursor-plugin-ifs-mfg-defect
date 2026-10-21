# Manufacturing trace map

Start here for shop order / material / DOP tickets, then follow actual callers. Do not invent flows that the code does not reach.

## Component / LU map

| Area | Component | Typical LUs / files |
|------|-----------|---------------------|
| Shop order | `shpord` | `ShopOrd`, `ShopMaterialAlloc`, `ShopMaterialAllocList`, operations |
| DOP supply | `dop` | `DopSupplyPurchOrd` and related DOP supply |
| CTP / order structure | `ordstr` | `InterimCtpManager` |
| Inventory / purchasing | follow traces | inventory + `purch` when the call chain leaves shpord/dop |

Lookup (this workspace is the track root):

```
model/<component>/<Name>.entity|.client|.projection
source/<component>/database/<Name>.plsql|.plsvc|.views
test/<component>/database/<Name>.pltst
```

## What to check on the defect path

- Shop order state vs material state (planned / released / reserved / issued / started supply).
- Pegging and supply type (shop, purchase, DOP, inventory).
- Multi-line / multi-component allocations (unique-constraint and quantity bugs).
- Clocking / labor history **only** if the ticket is WIP/labor — not on every material ticket.

## Related flows (Step 7)

Include a related flow in the matrix only when the fix actually executes on that path:

- Reserve / unreserve, issue / unissue
- Start / close shop order
- DOP supply and pegging
- Multi-component lines, other sites

If callers are unclear, ask the user.

## Functional docs (Step 3)

`https://docs.ifs.com/ifsclouddocs/<YYrX>/lang/en/`

Fetch the activity or page for Shop Order, Shop Order Materials, or DOP for the **reported version**. Use Explanation, Prerequisites, and System Effects.
