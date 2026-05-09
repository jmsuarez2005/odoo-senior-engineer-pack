---
name: odoo-data-import
description: Plan a data import / migration from a legacy system into Odoo 17 — partners, products, opening balances, historical orders. Use when migrating from another ERP/CRM, onboarding a new customer with existing data, or seeding a deployment.
---

You are planning a data import. Be paranoid: bad imports leave bad data forever.

## Inputs

`$ARGUMENTS` — what's being imported and source system. If absent, ask:

1. Source system (Excel, QuickBooks, SAP, custom DB, CSV dump…)
2. Volumes (number of partners, products, transactions)
3. Target Odoo version + edition
4. Required: customer-master, product-master, opening balances, transaction history, …
5. Cutover model: big-bang or phased?
6. Mappings already defined? (a draft is enough)

## Steps

1. Identify the **import scope**: which Odoo models will receive data, in which order.

2. Define the **import order** (critical):
   - Companies / partners FIRST
   - Products & categories
   - Chart of accounts (if from scratch)
   - Opening balances (journal entries)
   - Inventory opening (stock.quant or initial inventory adjustment)
   - Open transactions (open SOs, open POs, unpaid invoices)
   - Historical (closed) transactions — usually NOT imported, only reference data

3. For each model, plan:
   - Field mapping (source → Odoo)
   - Transformations (date format, currency, address splitting, …)
   - Validation rules
   - Idempotency: external_id strategy

4. Pick a **method** per model:
   - **Excel/CSV import via UI** — for ≤ 10K records, well-formed source
   - **`load()` method** — programmatic batch import with `external_id` deduplication
   - **`create()` in cron / queue_job** — for very large volumes with retries
   - **Direct SQL** — last resort; bypasses ORM and is risky

5. Always:
   - Use `external_id` (xml_id) for every imported record — enables re-imports
   - Run on a test DB first
   - Compare totals (count, sum) before vs after
   - Have a rollback plan

## Output

```markdown
## Data import plan

### Source → Odoo model map
| Source table | Odoo model | Volume | Method |
|---|---|---|---|

### Import order
1. `res.country` (if not standard)
2. `res.partner.industry` (if needed)
3. `res.partner` (companies before contacts via parent_id)
4. `product.category`
5. `product.template` then `product.product`
6. `account.account` (or use l10n module)
7. `account.move` for opening balances
8. `stock.quant` via inventory adjustment
9. Open SOs, POs, invoices

### Field mappings (per entity)
#### res.partner
| Source field | Odoo field | Transformation |
|---|---|---|

(repeat per entity)

### Transformations
- Dates: <source format> → ISO
- Currency: <source code> → res.currency.id
- Addresses: split into street, city, state_id, country_id
- Phone: normalize to E.164
- Tax IDs: validate format per country

### External ID strategy
- Prefix: `legacy.` (e.g. `legacy.partner_12345`)
- Stored on each imported record's `id` column via `xml_id`
- Re-importable: same source row → same external_id → upsert via `load()`

### Validation
| Check | Expected | Method |
|---|---|---|

Examples:
| Total partners | <source count> | `search_count` after import |
| Sum of AR | <source AR balance> | `account.move.line.sum` after opening balance import |

### Test plan
1. Import dataset on staging DB
2. Run validation queries
3. Spot-check 10 random records vs source
4. Have an end user log in and find their records
5. Run the standard reports — do balances match source?

### Cutover
- T-7 days: final test import on staging
- T-1 day: freeze source system
- T-0 (cutover): final extract → import → validate → go live
- T+7 days: monitor for issues, hot-fix as needed

### Rollback
- DB snapshot before final import
- Documented `unlink` or restore-from-snapshot procedure
- Keep source extract available for re-runs

### Risks
- <data quality risks>
- <timing / cutover risks>
- <volume / performance risks>
```

## Quality bar

- Always run on staging before production.
- Use `load()` with `external_id` for batch + idempotency.
- Never `unlink` followed by re-create — use upsert via external_id.
- Validate by **counting and summing** before and after, not by spot checks alone.
- Keep the source extract immutable; treat it like a backup of the legacy system.

## What NOT to do

- Don't write directly to DB tables. Use ORM.
- Don't skip `external_id` — re-imports become impossible.
- Don't import historical transactions if you don't have to. Reference data + opening balances are usually enough.
- Don't forget multi-company: every model with `company_id` needs explicit company assignment.
- Don't trust source data formatting. Validate every column.
- Don't run a 1M-record import in a single transaction. Batch with `cr.commit()`.
