---
name: business-subscriptions
description: Odoo 17 Subscriptions (sale_subscription Enterprise / OCA subscription_oca) — recurring revenue, MRR, ARR, plans, billing, churn, upgrades/downgrades. Use when configuring SaaS-style billing, recurring services, or building subscription-aware reporting.
---

# Business: Subscriptions (Odoo 17)

## What this app solves

Recurring revenue:
- **Plans** (templates with line items + frequency)
- **Subscriptions** (a customer's instance of a plan)
- **Invoicing** (auto-generated each cycle)
- **Upgrades / downgrades / proration**
- **Churn** (cancellation, suspension)
- **MRR / ARR** dashboards

`sale_subscription` is **Enterprise**. Community alternative: OCA `subscription_oca` / `contract_oca`.

## Core models (Enterprise)

| Model | Purpose |
|---|---|
| `sale.order.template` (with recurrence) | Plan template |
| `sale.order` (with `is_subscription = True`) | Subscription instance |
| `sale.order.line` (with recurrence) | Recurring line |
| `sale.order.alert` | Health rules ("price drop alert", "expiring") |
| `account.move` | Generated invoices |

In v17 the model split changed: subscriptions are now `sale.order` records with subscription-specific fields (not a separate `sale.subscription` model as in earlier versions). The `subscription_state` field tracks lifecycle.

## Lifecycle (`subscription_state`)

`draft` → `1_draft` → `2_renewal` → `3_progress` → `4_paused` → `5_renewed` → `6_churn`

Renewal: when a subscription's "next invoice date" is reached, the cron creates an invoice. If auto-renewal is on and payment succeeds, subscription continues.

## Configuration

### Templates
- Recurrence rule (daily / monthly / quarterly / yearly)
- Auto-close after N missed payments
- Self-service options (customer can upgrade/cancel from portal)
- Default products (plan tiers)
- Currency, pricelist

### Recurrence on product
Products marked as "recurring" are billable on the subscription cycle. Set `recurring_invoice = True`.

### Payment provider with token (off-session)
For auto-pay, payment provider must support token storage. Stripe, Adyen, Authorize.net all do.

## Customizations

### Custom plan tiers with auto-upgrade
"If usage > X, auto-upgrade to next tier":

```python
class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _cron_check_usage_upgrades(self):
        active = self.search([("subscription_state", "=", "3_progress")])
        for sub in active:
            usage = self.env["my.usage.metric"].read_group(
                [("subscription_id", "=", sub.id), ("date", ">=", sub.last_invoice_date)],
                ["units:sum"], [],
            )[0]["units"]
            if usage > sub.tier_limit:
                sub._upgrade_to_next_tier()
```

### Proration on upgrade
Standard handles upgrades within a cycle by creating a credit + new invoice, prorated. To customize the proration formula:

```python
def _compute_prorated_amount(self, days_remaining, days_in_cycle, full_amount):
    # default: linear
    return full_amount * days_remaining / days_in_cycle
```

Override for "minimum 30% even if half-cycle" or other rules.

### Dunning (failed payment retries)
Standard retries auto-renewal failures with configurable delays. Customize email templates per retry attempt:

```xml
<record id="mail_template_dunning_1" model="mail.template">
    <field name="name">Subscription: 1st payment failure</field>
    <!-- friendly first reminder -->
</record>
<record id="mail_template_dunning_3" model="mail.template">
    <field name="name">Subscription: final notice before suspension</field>
    <!-- urgent -->
</record>
```

### Usage-based billing
Pure subscription = fixed monthly fee. Hybrid = base + usage (per-API-call, per-user-active, etc.):

```python
class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    is_usage_based = fields.Boolean()
    usage_qty = fields.Float()  # accumulated usage, reset on invoice

    def _compute_qty_to_invoice(self):
        for line in self:
            if line.is_usage_based:
                line.qty_to_invoice = line.usage_qty
                continue
            super(SaleOrderLine, line)._compute_qty_to_invoice()
```

A separate metering system (cron from event log) updates `usage_qty`.

## MRR / ARR analysis

Standard: subscription dashboard with MRR over time, churn rate, retention cohort.

Custom: "Net revenue retention by cohort" — join subscriptions started in month N with their revenue 6/12/18 months later.

## Common pitfalls

- Subscription with payment provider that doesn't support tokens → manual invoicing only.
- Customer cancels mid-cycle but still gets billed (not refunded) — clarify policy in T&Cs and reflect in code.
- Multi-currency subscriptions where currency rate changes mid-period → use `currency_id` consistently from sub creation.
- Custom upgrade logic that creates a new SO instead of editing — duplicate billing risk.
- Customer email change mid-subscription → make sure portal access tied to current email.
- Cron not running → subscriptions never bill. Monitor cron success.
- Soft-deleting subscriptions → MRR ghosts. Use `state = "6_churn"`, never `unlink`.

## OCA alternatives

If no Enterprise:
- `subscription_oca` — basic recurring sales
- `contract_oca` — more flexible (per-line recurrence, prorations)
- `account_invoice_subscription` — invoice-side recurrence
- `subscription_management` — older but stable

## References

- [Odoo Subscriptions documentation](https://www.odoo.com/documentation/17.0/applications/sales/subscriptions.html)
- [OCA contract](https://github.com/OCA/contract)
