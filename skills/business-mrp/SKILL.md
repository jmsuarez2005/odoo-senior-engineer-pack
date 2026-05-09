---
name: business-mrp
description: Odoo 17 Manufacturing (mrp) — BOMs, work centers, routing, manufacturing orders, work orders, MRP scheduler, kits, by-products, subcontracting, quality. Use when configuring production, customizing BOMs, integrating with shop floor, scheduling MOs, or modeling subcontracted manufacturing.
---

# Business: Manufacturing (Odoo 17 — `mrp`)

## What this app solves

Plan and execute production:
- Define **Bills of Materials** (recipes)
- Plan **Manufacturing Orders** (MOs)
- Execute **Work Orders** at **Work Centers**
- Track raw material consumption + finished goods production
- **Subcontracting** to external manufacturers
- **Kits** (logical bundles, no actual production step)
- **By-products** (multiple outputs from one process)
- **Quality** checks at any step

Connects with Inventory (component reservation, finished good in stock), Purchase (raw material procurement), Sale (MTO products).

## Core models

| Model | Purpose |
|---|---|
| `mrp.bom` | Bill of Materials |
| `mrp.bom.line` | Component line in a BOM |
| `mrp.bom.byproduct` | By-product line |
| `mrp.production` | A Manufacturing Order (MO) |
| `mrp.workcenter` | A station / machine / cell |
| `mrp.routing.workcenter` | Operation in a BOM (routing step) |
| `mrp.workorder` | Execution of a routing operation for a specific MO |
| `quality.check` | Inspection check (with `quality` module) |

## BOM types

`type` field on `mrp.bom`:
- `normal` — standard manufacturing BOM (creates an MO)
- `phantom` (kit) — logical bundle; sale of the kit creates moves for components, no MO
- `subcontract` — produced externally; sale triggers a PO to subcontractor with components

`product_id` on the BOM = what's produced. `product_tmpl_id` for variants.

## Manufacturing Order lifecycle

`draft` → `confirmed` (components reserved) → `progress` (work orders started) → `to_close` → `done` / `cancel`

The MRP scheduler (cron `mrp.production._procurement_scheduler`) propagates demand:
- A sale order needs a manufactured product not in stock
- Procurement creates a draft MO (per the BOM)
- Components needed → either reserved from stock or trigger child procurement (PO or sub-MO)

## Configuration

### Products
- Type = "Storable" (for finished goods we track)
- Route = "Manufacture" (or both Manufacture + Buy)
- Production Lead Time (days from MO to ready)
- Manufacturing Lead Time on the BOM

### Work centers
- Capacity (units per hour)
- OEE target (Overall Equipment Effectiveness)
- Time efficiency (factor for time tracking)
- Cost per hour (drives MO costing)

### Routings (operations)
On the BOM: list of `mrp.routing.workcenter` lines, each with:
- Operation name (Cut, Drill, Assemble, Pack)
- Work center
- Expected duration (manual or computed from past)

### Quality checks
With `quality` module: define check types (instructions, measure, pass/fail, picture). Link to picking types or work centers. Triggered at receipt, transfer, or production.

## Common customizations

### Multi-level BOM (sub-assemblies)
Standard. Define a BOM for the sub-assembly product, then add it as a component in the parent BOM. The MRP scheduler creates child MOs as needed.

### Configurable products with attribute-based BOMs
Standard: BOM lines can have `bom_product_template_attribute_value_ids` — line "Carbon frame" only used for variant with attribute "Frame=Carbon". Configure in BOM editor.

For more dynamic configuration (per-customer BOMs), inherit `mrp.bom._bom_find` to pick the right BOM based on context.

### Subcontracting
Standard: BOM type = `subcontract`, set `subcontractor_ids` (vendor partners). Then:
- Sale of the product → PO to subcontractor
- PO confirms → backorder for components to ship to subcontractor
- Receipt from subcontractor → finished good comes in, components consumed automatically

To customize "what to ship with the order to subcontractor", inherit the procurement rule for subcontracts.

### Custom work order screen
The "tablet view" for shop floor uses OWL components. To customize (e.g. display extra fields, add a custom button per work center type):

```python
class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    def action_custom_action(self):
        # custom logic
        ...
```

```js
// Inherit the OWL component for the work order screen
patch(WorkorderScreen.prototype, {
    setup() {
        super.setup();
        // additions
    },
});
```

### Quality alerts
The `quality_control` module lets you raise alerts. To auto-raise alerts on certain conditions (e.g. dimension out of spec):

```python
@api.constrains("measured_value")
def _check_spec(self):
    for check in self:
        if check.norm_min and check.measured_value < check.norm_min:
            self.env["quality.alert"].create({
                "product_id": check.product_id.id,
                "title": _("Out of spec on %s") % check.name,
                "team_id": check.team_id.id,
            })
```

### MES integration (shop floor data)
Export work order start/end + measurements to an MES via webhook:

```python
def button_start(self):
    res = super().button_start()
    self.with_delay()._push_to_mes("started")
    return res
```

Use `queue_job` for async.

### Scrap and waste tracking
`stock.scrap` records material loss. Custom reports often need scrap-by-reason or scrap-by-shift dimensions — extend `stock.scrap` with custom fields and group reporting.

## Reports & dashboards

Standard:
- Manufacturing Order PDF
- Work Order PDF
- BOM Structure & Cost (drills down through sub-BOMs)
- MRP analysis

Common customs:
- "Production schedule view" — gantt of MOs by work center
- "Variance report" — planned vs actual for materials and time

## Integration touchpoints

| Pattern | Approach |
|---|---|
| **Sale → MO** | MTO products with route=Manufacture create draft MO |
| **MRP scheduler** | Daily cron generates/refreshes draft MOs and POs |
| **Tablet view → MES** | Custom OWL screen pushes events |
| **External ERP for production data** | Webhook receives "MO done" with measurements; updates Odoo |
| **MO → Account** | On done, valuation layers post material consumption + production at standard/AVCO |

## Common pitfalls

- Forgetting BOM `product_id` (for variants) vs `product_tmpl_id` (for templates) — BOM not found at MO creation.
- Phantom (kit) BOM with stockable components but no replenishment route — sale fails because components are missing and no MO exists to make them.
- Subcontracted product without `subcontractor_ids` — standard purchase flow runs instead of subcontract flow.
- Custom field on `mrp.production` not propagated to `mrp.workorder` when needed — adjust the workorder creation hook.
- Work center capacity miscalibrated — schedule gives wildly off lead times.
- Operating without quality checks → no audit trail when defects appear.
- Direct `stock.move` creation around an MO instead of using consume/produce buttons → MO state stays incorrect.

## OCA modules worth knowing

- `mrp_production_request` — request production without creating MOs directly
- `mrp_workorder_sequence` — control work order ordering
- `mrp_subcontracting_dropshipping` — subcontract drop-ship combo
- `mrp_bom_tag` — categorize BOMs
- `mrp_multi_level` — multi-level MRP with consolidated views
- `mrp_warehouse_calendar` — workcenter calendar per warehouse

## References

- [Odoo Manufacturing documentation](https://www.odoo.com/documentation/17.0/applications/inventory_and_mrp/manufacturing.html)
- [OCA manufacture](https://github.com/OCA/manufacture)
