---
name: business-accounting
description: Odoo 17 Accounting (account, account_accountant) — chart of accounts, journals, double-entry, taxes, fiscal positions, payment, reconciliation, multi-currency, fiscal localizations. Use when configuring accounting, building custom reports, integrating payment providers, customizing invoice flow, or troubleshooting reconciliation.
---

# Business: Accounting (Odoo 17 — `account` / `account_accountant`)

## What this app solves

Full double-entry accounting:
- Chart of accounts per company
- Journals (sales, purchase, bank, cash, miscellaneous)
- Customer invoices and vendor bills
- Payments and reconciliation
- Taxes (VAT, sales tax, withholding) with fiscal positions
- Multi-currency
- Fiscal periods, lock dates, audit trail
- Country-specific localization (`l10n_es`, `l10n_fr`, `l10n_mx`, `l10n_us`, etc.)

Two flavors:
- `account` (Community) — invoicing + basic accounting
- `account_accountant` (Enterprise) — adds full accounting features (consolidation, advanced reporting, asset management, tax reports)

## Core models

| Model | Purpose |
|---|---|
| `account.move` | A journal entry (also: invoice, bill, refund) |
| `account.move.line` | A debit/credit line in an entry |
| `account.account` | A GL account (asset, liability, etc.) |
| `account.journal` | A journal (Customer Invoices, Bank, Cash) |
| `account.tax` | A tax definition |
| `account.fiscal.position` | Tax remapping rules (per country, per partner) |
| `account.payment` | A payment (in or out) |
| `account.payment.term` | Payment terms (Net 30, etc.) |
| `account.reconcile.model` | Bank reconciliation rules |
| `account.analytic.account` / `account.analytic.line` | Cost accounting dimension |

`account.move` is **the** central object. An invoice is a move; a bill is a move; a manual journal entry is a move. The `move_type` field distinguishes:
- `out_invoice` — customer invoice
- `out_refund` — credit note
- `in_invoice` — vendor bill
- `in_refund` — vendor credit note
- `entry` — miscellaneous journal entry

## State lifecycle

`draft` → `posted` → optionally `cancel`.

After posting:
- Move lines are immutable (audit-safe).
- The move increases the journal's running balance.
- Numbers are assigned from the journal's sequence.

## Configuration — what the consultant sets up

### Chart of accounts (CoA)
Choose a localization (`l10n_es`, `l10n_fr_pcg`, etc.). The CoA installs automatically with all the country-specific accounts, taxes, fiscal positions.

Don't build your own CoA from scratch. The localizations are hundreds of person-hours of legal research per country.

### Journals
- **Customer Invoices** — sales journal, posts to revenue + AR
- **Vendor Bills** — purchase journal, posts to expense + AP
- **Bank** — one per bank account; supports import (CSV, OFX, MT940, CAMT.053)
- **Cash** — petty cash with reconciliation
- **Miscellaneous** — for adjustments, accruals, reclassifications

Each journal has:
- Default debit/credit accounts
- Sequence (separate sequence per journal!)
- Allowed accounts (whitelist)
- Default partner (for bank statements)

### Taxes
- Define per company
- `amount_type`: `percent`, `fixed`, `division`, `group` (combination)
- `type_tax_use`: `sale`, `purchase`, `none`
- Tax tags map to financial report lines
- Country-specific behaviors via `country_id`

### Fiscal positions
The "if-then" engine for taxes:
- "If customer is in EU + has VAT number → swap 21% VAT with 0% intra-EU"
- "If customer is outside EU → swap 21% VAT with 0% export"
- "If account 4070 (domestic revenue) maps to 4071 (foreign revenue) for this customer"

Configure tax mappings AND account mappings on `account.fiscal.position`.

### Payment terms
"Net 30", "50% on signature, 50% within 30 days", "End of month + 30 days". Each `account.payment.term.line` defines a percentage and offset.

### Bank synchronization (Enterprise)
- Connect via Odoo Online to thousands of banks (Plaid-like aggregator integration)
- Or upload bank statements (CSV / OFX / CAMT)
- Reconciliation models (rules) match incoming lines to existing invoices

## Common customizations

### Custom invoice numbering
Standard: per-journal sequence (e.g. `INV/2026/0001`). To customize:
- Edit the journal's sequence in Settings > Technical > Sequences
- Or add a custom prefix per company / per tax payer

For more complex (e.g. per fiscal year reset, per branch), inherit `account.move._post`:

```python
class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        for move in self:
            if move.move_type == "out_invoice" and not move.name:
                # custom numbering logic before super assigns the default
                ...
        return super()._post(soft=soft)
```

But: Odoo's sequence handling is solid. Most "custom numbering" requests are reframable as configuration.

### Locking past periods
Standard `lock_date` on `res.company`. Once set, no one (not even admin) can post to a date ≤ lock date. Use this every month-end.

### Custom approval flow on bills
Common for accounts payable. Use OCA `account_invoice_supplierinfo_update` + `account_invoice_three_way_match` (3-way match: bill, PO, receipt) or build:

```python
class AccountMove(models.Model):
    _inherit = "account.move"

    state = fields.Selection(selection_add=[
        ("to_approve", "Pending approval"),
    ], ondelete={"to_approve": "set draft"})

    def action_post(self):
        for move in self:
            if move.move_type == "in_invoice" and move.amount_total > 5000 and move.state == "draft":
                move.state = "to_approve"
                move.activity_schedule(...)
                continue
            super(AccountMove, move).action_post()
```

### Custom analytic distribution
v17 made analytic distribution **a JSON field on lines** (not a separate o2m). Distribution per line:
```python
line.analytic_distribution = {
    str(analytic_account_id_1): 60.0,
    str(analytic_account_id_2): 40.0,
}
```

Custom rules (e.g. auto-distribute by department) extend `_compute_analytic_distribution` on the line.

### Recurring invoices / subscriptions
Use `sale.subscription` (Enterprise) or OCA `subscription_oca`. Don't roll your own — recurring invoicing has many edge cases (proration, mid-cycle changes, currency, taxes).

### Custom reports (P&L breakdown, AR aging by team, etc.)
Enterprise has `account_reports` with a JSON-defined report engine. Custom rows/columns are configured, not coded.

For Community, build with QWeb on top of `account.move.line` queries.

### Multi-currency
- Each `res.currency` has rates (`res.currency.rate` records, daily)
- Move lines store `amount_currency` (in the line's currency) AND `debit`/`credit` (in company currency)
- Bank reconciliation handles FX gain/loss automatically when posting payment in different currency from invoice

If you customize, **never** compute amounts in your own currency conversion — use `currency_id._convert(amount, target, company, date)`.

## Common patterns: integrations

| Pattern | Approach |
|---|---|
| **Payment gateway (Stripe, PayPal)** | Use `payment` framework; install `payment_stripe`, `payment_paypal`. Custom = inherit `payment.provider` |
| **External invoicing system → Odoo** | Webhook → create `account.move` in `draft` state, post in queue_job |
| **Bank import** | Use bank statement import wizards or aggregator (Enterprise). For custom bank format, write a parser inheriting `account.bank.statement.import` |
| **Tax authority filing (e.g. SII Spain, FATCA, GST)** | Use the country's localization module (`l10n_es_aeat`, `l10n_in_gst`, etc.). Don't build from scratch |

## Reconciliation

Reconciliation is matching invoice lines with payment lines so AR/AP balances clear. Three flavors:

1. **Bank statement reconciliation** — auto-match incoming bank line to existing invoice/payment via `account.reconcile.model` rules
2. **Manual reconciliation** — match move lines on the same account
3. **Auto-reconcile** — cron-based for repeating patterns

Custom reconcile rules: extend `account.reconcile.model` or write a cron that periodically matches based on your business logic.

## Key business rules (don't break these)

- **Debits = credits per move.** Always. Odoo enforces it; if you write to lines, keep balance.
- **Posted moves are immutable.** Don't try to "fix" them with `unlink` or direct SQL. Use credit notes (`out_refund` / `in_refund`).
- **Sequence integrity.** Don't manipulate `name` on posted moves.
- **Per-company isolation.** All accounting models are multi-company. Always set `company_id`.
- **Currency rate dates matter.** Conversion uses the rate at the move's date, not "now."

## OCA modules worth knowing

- `account_financial_report` — better community-grade reports
- `account_payment_order` — payment batching (like SEPA, ACH)
- `account_banking_sepa_direct_debit` — SEPA DD mandates and orders
- `account_invoice_three_way_match` — three-way match for payables
- `account_lock_date_update` — manage lock dates per role
- `account_reconcile_oca` — improved reconcile UX
- `mis_builder` — custom report builder

## Common pitfalls

- Adding a custom field to `account.move` that breaks export to country e-invoicing (some country localizations expect fixed schemas).
- Skipping `account.fiscal.position` and hardcoding tax IDs → breaks for foreign customers.
- Direct UPDATE on `account_move_line` → corrupts balance, breaks reports.
- Custom numbering that violates per-fiscal-year continuity (legally required in many countries: Spain, France, Italy).
- Allowing posting to a journal with no sequence (Odoo allows it but you'll regret it).
- Using `sudo()` to post moves "for the user" → audit trail says system did it, not the user. Use `with_user(user)` if you really need to act on their behalf.
- Forgetting the `lock_date` on closed periods → bookkeepers post to closed months by accident.

## References

- [Odoo Accounting documentation](https://www.odoo.com/documentation/17.0/applications/finance/accounting.html)
- [OCA account-financial-tools](https://github.com/OCA/account-financial-tools)
- [OCA account-financial-reporting](https://github.com/OCA/account-financial-reporting)
- [Country localizations](https://www.odoo.com/documentation/17.0/applications/finance/fiscal_localizations.html)
