---
name: odoo-localize
description: Set up an Odoo 17 localization for a country — chart of accounts, taxes, fiscal positions, payroll structure, e-invoicing. Use when configuring a new country deployment or auditing a localization for compliance.
---

You are configuring or auditing the country-specific setup for an Odoo deployment.

## Inputs

`$ARGUMENTS` — country code (ISO-2: ES, FR, MX, US, …) and optionally what's needed (`accounting`, `payroll`, `e-invoicing`, `all`).

If absent, ask:
1. Which country?
2. What's the legal entity type (corporation, sole prop, branch)?
3. Which sub-modules: accounting, payroll, e-invoicing, intrastat, …?
4. Existing chart of accounts to preserve, or fresh install?

## Steps

1. Identify the right `l10n_<country>` modules:
   - `l10n_<cc>` — chart of accounts + taxes + fiscal positions
   - `l10n_<cc>_hr_payroll` — payroll structures
   - `l10n_<cc>_edi` — e-invoicing format / authority
   - `l10n_<cc>_reports` — country-specific tax reports (Enterprise)

2. Audit / install order:
   - Install on a fresh DB or test branch FIRST
   - Verify chart of accounts loaded correctly
   - Verify taxes match current legal rates
   - Verify fiscal positions cover B2B domestic, intra-EU, export
   - Verify payroll rules (if applicable) match latest legal updates

3. Common configuration after install:
   - Set company VAT number, registration number
   - Configure withholdings (if applicable)
   - Set up legal sequences (for invoices, credit notes)
   - Configure lock dates per fiscal period
   - Set up e-invoicing certificates / API credentials

4. Identify gaps if any. Common ones:
   - Recent law change not reflected in standard module yet
   - Unusual tax (small business exemption, tourist tax) not modeled
   - Specific report format not in core (use OCA)

## Output

```markdown
## Localization plan: <country>

### Modules to install (in order)
1. `l10n_<cc>` — base CoA + taxes
2. `l10n_<cc>_<extra>` — ...
3. `l10n_<cc>_reports` — (if Enterprise)

### Configuration after install
| Setting | Where | Value |
|---|---|---|

### Sequences (legal numbering)
| Document | Sequence | Format requirement |
|---|---|---|

### Tax rates (verify)
| Tax | Rate | Use |
|---|---|---|

### Fiscal positions to verify
| Position | Maps |
|---|---|

### E-invoicing setup (if applicable)
- Authority: <name>
- Format: <UBL / FacturaE / FatturaPA / SAT / …>
- Required fields: <list>
- Certificate / credentials needed
- Test environment URL

### Known gaps / OCA modules to add
| Gap | Solution |
|---|---|

### Validation checklist
- [ ] Test invoice posts cleanly to the right accounts
- [ ] Tax report matches manual calc for sample period
- [ ] Foreign customer invoice picks intra-EU / export correctly
- [ ] Payroll: sample payslip matches expected legal calc (if applicable)
- [ ] E-invoicing test sends to authority sandbox successfully (if applicable)

### Documentation links
- Official Odoo docs for <country>
- Tax authority website
- OCA <country> repository (if exists)
```

## Quality bar

- Always reference the **specific** modules by technical name.
- Validate against a real example (one invoice, one payslip) — never assume.
- Track recent legal changes (e.g. e-invoicing mandates have been rolling out 2024-2026 in EU).
- Don't recommend hand-rolling tax rules when a localization module exists.
- Note Enterprise-only features clearly.

## What NOT to do

- Don't bypass the localization module to "simplify" — you'll re-implement years of legal compliance work.
- Don't hardcode tax rates or account codes in custom modules. Reference via xmlid.
- Don't skip `account.fiscal.position` — it's the engine for non-domestic transactions.
- Don't deploy to production without running a sample of the country's required tax reports.
