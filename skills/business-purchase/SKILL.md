---
name: business-purchase
description: Odoo 17 Purchase (purchase) — RFQs, purchase orders, vendor pricelists, agreements, blanket orders, three-way match, vendor bills. Use when configuring procurement, customizing approval flows, vendor evaluation, multi-warehouse purchasing, or purchase-to-pay integration.
---

# Business: Purchase (Odoo 17 — `purchase`)

## What this app solves

Procurement: from request for quotation (RFQ) to vendor bill:
- Send RFQs to vendors, compare offers
- Confirm Purchase Orders
- Receive goods (links to Inventory)
- Match to vendor bills (links to Accounting)
- Vendor agreements / blanket orders for long-term commitments
- Vendor pricelists per quantity / per supplier

## Core models

| Model | Purpose |
|---|---|
| `purchase.order` | RFQ / PO header |
| `purchase.order.line` | Line item |
| `purchase.requisition` | Vendor agreement / blanket / call for tender |
| `product.supplierinfo` | Vendor pricelist row (this vendor sells this product at this price/lead time) |
| `res.partner` (with `supplier_rank > 0`) | Vendor |

## State lifecycle

`draft` → `sent` (RFQ sent to vendor) → `to approve` (optional approval gate) → `purchase` (confirmed PO) → `done` / `cancel`

After confirmation:
- Reception pickings created (if products are storable)
- Vendor bill drafted (when product invoicing policy = "On ordered" or after receipt)

## Configuration

### Vendor settings on partner
- `supplier_rank > 0` → recognized as vendor
- Default payment terms, fiscal position
- Bank accounts

### Product procurement settings
- Route = "Buy"
- Vendor pricelist (`product.supplierinfo`) — which vendors sell it, at what price, lead time
- Purchase tax (per company)
- Description for vendors (translated)

### RFQ approval workflow
Standard: orders > a configurable amount go to "to approve". Configure in Settings:
- Purchase > Levels of Approval = "All Orders" or "By Amount"
- Threshold per company

For complex flows (multi-step, by category, by user), build:

```python
class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    state = fields.Selection(selection_add=[
        ("manager_approval", "Manager approval"),
        ("director_approval", "Director approval"),
    ], ondelete={"manager_approval": "cascade", "director_approval": "cascade"})

    def button_confirm(self):
        for order in self:
            if order.amount_total > 50000:
                order.state = "director_approval"
                # schedule activity
                continue
            if order.amount_total > 10000:
                order.state = "manager_approval"
                continue
            super(PurchaseOrder, order).button_confirm()
```

## Common customizations

### Three-way match (PO + GR + Bill)
The standard `purchase.order` shows received and billed quantities per line. Block over-billing or under-receipt:

```python
class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        for move in self.filtered(lambda m: m.move_type == "in_invoice"):
            for line in move.invoice_line_ids:
                po_line = line.purchase_line_id
                if po_line and line.quantity > po_line.qty_received:
                    raise UserError(_(
                        "Cannot bill more than received: %s > %s on %s",
                        line.quantity, po_line.qty_received, line.product_id.name,
                    ))
        return super()._post(soft=soft)
```

OCA `account_invoice_three_way_match` provides a fuller implementation.

### Auto-vendor selection
Standard: `_select_seller()` picks the cheapest matching vendor by default. For more complex (preferred vendor, geographic match, MOQ-aware):

```python
class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _select_seller(self, partner_id=False, quantity=0.0, date=None, uom_id=False, params=False):
        # Custom selection logic
        sellers = self.seller_ids.filtered(...)
        if not sellers:
            return super()._select_seller(...)
        return sellers[0]
```

### Blanket orders / framework agreements
Use `purchase.requisition` (need to install `purchase_requisition`). Vendor agrees to terms; specific POs draw down against the agreement.

### Vendor scoring / evaluation
Custom model `purchase.vendor.score`:
- On-time delivery rate
- Quality reject rate
- Price competitiveness

Computed nightly from `stock.picking` (delivery dates) + `quality.alert` (rejects). Used to filter `_select_seller`.

### Drop-shipping
Standard: route "Dropship" — sale → PO directly to supplier with customer's delivery address, supplier ships to customer. Configure on product.

### Currency on POs
Vendors can be priced in foreign currency. PO currency = vendor's pricelist currency. Conversion to company currency for accounting happens on bill posting.

## Reports & dashboards

Standard:
- RFQ / PO PDF
- Purchase analysis (`purchase.report`)
- Lead time analysis

Common customs:
- "Top vendors by spend" — read_group on PO confirmed
- "Open POs by aging" — POs in `purchase` state, days since receipt expected

## Integration touchpoints

| Pattern | Approach |
|---|---|
| **MRP → Purchase** | MRP scheduler creates draft POs for components when "Buy" route applies |
| **Stock → Purchase** | Reordering rules trigger PO creation when stock low |
| **Sale → Purchase (drop-ship)** | MTO + drop-ship route creates PO from SO |
| **Purchase → Vendor portal** | Standard portal lets vendors see/confirm POs |
| **EDI integration** | Custom controller receives EDI 850/855/856 → creates/updates POs |
| **Procurement aggregator (e.g. Coupa)** | Webhook for approved requisitions → create POs in Odoo |

## Common pitfalls

- Vendor pricelist with no `min_qty` — Odoo picks any line; results inconsistent. Always set `min_qty=0` on the catch-all line.
- Currency mismatch between PO and vendor's preference — PDF shows wrong currency; rate at posting time fixes accounting.
- Approval flow that bypasses on `button_draft` → user circumvents by editing.
- Manual PO line creation without `product_id` — breaks three-way match (no qty_received tracking).
- Vendor with multiple emails — Odoo sends to default; use `partner_id.message_post` with explicit recipient.
- Custom approval that leaves orders stuck in custom state with no auto-transition → invisible to users.

## OCA modules worth knowing

- `purchase_requisition_tier_validation` — multi-tier approval
- `purchase_request` — internal purchase requisition (employee asks to buy)
- `purchase_blanket_order` — blanket POs with call-offs
- `purchase_order_supplierinfo_update` — auto-update vendor pricelist from PO prices
- `purchase_three_way_match` — receipt + bill + PO match enforcement
- `purchase_landed_cost` — split PO landed costs across receipts

## References

- [Odoo Purchase documentation](https://www.odoo.com/documentation/17.0/applications/inventory_and_mrp/purchase.html)
- [OCA purchase-workflow](https://github.com/OCA/purchase-workflow)
