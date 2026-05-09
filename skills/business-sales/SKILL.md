---
name: business-sales
description: Odoo 17 Sales (sale_management) — quotations, sales orders, pricelists, discounts, delivery integration, sale_timesheet, commissions, customizations. Use when configuring or customizing the order-to-cash flow, quotation templates, multi-step approval, custom pricing, or commission calculation.
---

# Business: Sales (Odoo 17 — `sale_management`)

## What this app solves

The order-to-cash backbone for B2B (and the back-end of B2C). It models:

- **Quotation** — a proposed sale; can be sent, signed, expired
- **Sales Order** — confirmed quotation; triggers delivery, invoicing, optionally manufacturing
- **Customer** — a `res.partner`
- **Product / Variant** — what's sold; has prices, taxes, costs
- **Pricelist** — version-able pricing rules per customer/segment/quantity
- **Tax** — applied per line based on product + customer fiscal position
- **Delivery** — links to `stock.picking` (warehouse out)
- **Invoice** — links to `account.move` (the actual financial document)

It's the hub that connects CRM (lead → opportunity → quote), Inventory (order → delivery), Accounting (order → invoice → payment), and Manufacturing (order → MO).

## Core models (memorize these)

| Model | Purpose |
|---|---|
| `sale.order` | The quotation/order header |
| `sale.order.line` | Line items |
| `sale.order.template` | Quotation template (boilerplate + line list) |
| `product.template` | The "abstract" product (a t-shirt) |
| `product.product` | The variant (red, M) |
| `product.pricelist` | Pricing rules |
| `product.pricelist.item` | Individual rule (this product, this qty, this %) |
| `account.tax` | Tax rates and rules |
| `account.fiscal.position` | "If customer is in EU, swap tax X for Y" |
| `delivery.carrier` | Shipping methods |

## State lifecycle (`sale.order.state`)

`draft` → `sent` (quote sent to customer) → `sale` (confirmed) → `done` (locked) → `cancel`

After confirmation:
- `picking_ids` (delivery orders) get created based on the warehouse + product types
- `invoice_ids` get created based on the invoicing policy ("ordered quantities" or "delivered quantities")

## Configuration — what the consultant sets up

### Per company
- Default warehouse, default sales team, default analytic plan
- Quotation expiration default
- Online signature & payment toggles
- Lock confirmed orders (locks editing after confirmation)

### Per product
- Sales tax (per company, per fiscal position)
- Invoicing policy (ordered vs delivered)
- Routes (Make to Order vs Make to Stock)
- Income account (override of category default)
- Description for quotations (richtext)

### Pricelists
A `product.pricelist` has `item_ids` — rules like:
- 10% off for product category "Shoes" if quantity ≥ 10
- Fixed price 50€ for product "T-shirt M" for partner segment "Distributors"
- Price = 80% of cost for partner "Internal sales"

Pricelists support **versions** (effective date ranges) and **multiple-currency** by linking to currency.

### Quotation templates
`sale.order.template` lets you save a recurring set of lines + terms + recurring price. Sales reps pick a template when creating a quote; lines auto-populate.

## Common customizations & how to do them

### Custom approval workflow ("orders > 10K need manager OK")

Standard: `sale.order` confirms in one step. To insert approval:

```python
class SaleOrder(models.Model):
    _inherit = "sale.order"

    state = fields.Selection(selection_add=[
        ("to_approve", "Pending approval"),
        ("approved", "Approved"),
    ], ondelete={"to_approve": "cascade", "approved": "cascade"})

    def action_confirm(self):
        for order in self:
            if order.amount_total > 10000 and order.state != "approved":
                order.state = "to_approve"
                order.activity_schedule(
                    "mail.mail_activity_data_todo",
                    summary=_("Approve order > 10K"),
                    user_id=order.user_id.parent_id.id or order.user_id.id,
                )
                continue
            super(SaleOrder, order).action_confirm()
```

Don't blindly extend `state` — the values are referenced by views, reports, security. Use `selection_add` (the v17 way), and add views for the new states.

### Commission per salesperson on confirmation

Common ask. Pattern:

```python
class SaleOrder(models.Model):
    _inherit = "sale.order"
    commission_amount = fields.Monetary(compute="_compute_commission", store=True)
    commission_rate = fields.Float(related="user_id.commission_rate", store=True)

    @api.depends("amount_total", "commission_rate", "state")
    def _compute_commission(self):
        for order in self:
            order.commission_amount = (
                order.amount_total * order.commission_rate
                if order.state in ("sale", "done") else 0.0
            )
```

For real comp programs, OCA `commission` provides full structures (tiered rates, commission settlements, payments). Prefer it over reinventing.

### Custom delivery cost rules

Standard: `delivery.carrier` with rules. For more complex (zone × weight × volume), inherit `delivery.carrier` and override `_get_price_available_from_so`.

### Multi-step approval with custom roles

Use OCA `sale_order_approval` or build a `sale.approval.line` (one per step) tied to the order. State transitions check that all required approvals are in place.

### Project from sale (services billing)

Already built in: install `sale_timesheet` + `project`. A sale order line for a service product can auto-create a project + task on confirmation. Delivered quantities = logged timesheet hours, invoicing follows.

Configure: on the product, set type=Service, then "Service Tracking" → "Task in existing project" or "Project & Task".

## Reports & dashboards

Standard reports:
- Quotation / Order PDF
- Sales analysis (pivot/graph in `sale.report`)
- Salesperson performance dashboard

Adding a custom report (e.g. "Commissions by salesperson by month"): build on `sale.report` (a SQL view model) or create a new SQL model:

```python
class SaleCommissionReport(models.Model):
    _name = "sale.commission.report"
    _auto = False
    _description = "Commission Report"

    user_id = fields.Many2one("res.users", readonly=True)
    month = fields.Date(readonly=True)
    total_commission = fields.Monetary(readonly=True)
    currency_id = fields.Many2one("res.currency", readonly=True)

    def init(self):
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW sale_commission_report AS
            SELECT
                row_number() OVER () AS id,
                user_id,
                date_trunc('month', date_order)::date AS month,
                SUM(commission_amount) AS total_commission,
                currency_id
            FROM sale_order
            WHERE state IN ('sale', 'done')
            GROUP BY user_id, month, currency_id
        """)
```

Then build a pivot/graph view on it.

## Integration touchpoints

| Direction | Common patterns |
|---|---|
| **CRM → Sale** | `crm.lead.action_new_quotation()` creates a quotation linked to the opportunity |
| **Sale → Stock** | On confirm, `_action_launch_stock_rule()` creates pickings |
| **Sale → Account** | `_create_invoices()` generates draft invoices |
| **Sale → Project** | Service products with `service_tracking` create projects/tasks |
| **eCommerce → Sale** | `website_sale` creates draft sale orders from the cart |
| **External CRM (Salesforce, HubSpot) → Odoo** | Webhook receives lead → creates `crm.lead` (or `sale.order` for sale-stage syncs) |

## Common pitfalls

- Adding a state via `selection_add` but not handling it in `_action_confirm` → user can't move past it.
- Custom commission stored on `sale.order` line by line **and** on the order → drift. Pick one source of truth.
- Pricelist with overlapping rules → unpredictable price. Use `min_quantity` cleanly and order rules with `priority`.
- Building a "custom quotation report" by copying the standard one — fragile under upgrades. Inherit instead.
- Public eCommerce orders bypassing your custom approval logic — make sure your overrides cover both `_action_confirm` and any auto-confirm flows from `website_sale`.
- Multi-currency assumption: `amount_total` is in the order's currency; commissions in user currency. Convert via `currency_id._convert(...)`.
- Tax rounding: configure "round per line" vs "globally" at company level — affects invoice numbers and reconciliation.

## Localizations

Sale flows respect taxes via `account.fiscal.position`. The right tax for a French B2B vs intra-EU vs export is decided automatically when customer's country + the fiscal position rule match. Use Odoo's localization (`l10n_es`, `l10n_fr`, `l10n_mx`, etc.) — never hardcode tax rates.

## OCA modules worth knowing

- `sale_order_invoicing_grouping_criteria` — group invoices by criteria
- `sale_order_line_menu` — manage lines as their own list view
- `sale_quotation_number` — separate sequence for quotations vs orders
- `sale_blanket_order` — long-term commitments with call-offs
- `commission` — proper commission engine
- `sale_force_invoiced` — manually mark a line as invoiced

## References

- [Odoo Sales documentation](https://www.odoo.com/documentation/17.0/applications/sales/sales.html)
- [Sales developer reference](https://www.odoo.com/documentation/17.0/applications/sales/sales/products_prices/products.html)
- [OCA sale-workflow](https://github.com/OCA/sale-workflow)
