---
name: odoo-review
description: Senior-grade code review of an Odoo 17 module against Odoo official + OCA standards
---

You are doing a senior code review on an Odoo 17 module. Be thorough, specific, and constructive.

## Steps

1. Identify the module to review:
   - If `$ARGUMENTS` names a module, focus there.
   - Otherwise, ask the user which module or look for the module(s) in the current directory.

2. Read in this order:
   - `__manifest__.py`
   - `security/ir.model.access.csv` and `security/*.xml`
   - `models/*.py`
   - `views/*.xml`
   - `controllers/*.py` (if any)
   - `static/src/js/**/*.js` (if any)
   - `tests/*.py`

3. Run a checklist on each layer. For each issue, output: file:line — what's wrong — why it matters — suggested fix.

## Manifest checklist

- [ ] Version follows `17.0.X.Y.Z`
- [ ] License field present and one of the standard licenses
- [ ] Author includes "Odoo Community Association (OCA)" if OCA-style
- [ ] `summary` ≤ 100 chars
- [ ] `data` list ordered: security → data → views → reports
- [ ] `installable: True`
- [ ] `application` set deliberately (not `True` for sub-modules)
- [ ] `external_dependencies` only lists actual non-Odoo deps

## Security checklist

- [ ] Every model in `models/` has at least one row in `ir.model.access.csv`
- [ ] No row grants `perm_unlink=1` without justification
- [ ] Multi-company models have `company_id` field + global rule
- [ ] Every `sudo()` call has a comment explaining the trust boundary
- [ ] No `cr.execute` with f-strings or `%`-formatted values
- [ ] Public controllers (`auth="public"`) validate input before any DB write

## ORM checklist

- [ ] `@api.depends` on every computed field
- [ ] `_compute_*` methods set the field on **every** record in `self`
- [ ] No `for r in records: r.write({...})` loops (batch instead)
- [ ] `@api.model_create_multi` (not `@api.model` on `create`)
- [ ] `Many2one` fields: `ondelete=` set explicitly when not `restrict`
- [ ] `One2many` has its inverse `Many2one` defined
- [ ] `Monetary` has `currency_field` specified
- [ ] No `name_get` in new code (use computed `display_name`)
- [ ] `_description` set on every model

## View checklist (v17 specifics)

- [ ] No `<tree>` (use `<list>`)
- [ ] No `attrs="{...}"` (use direct attribute expressions)
- [ ] No `states="..."` on buttons (use `invisible="state not in ['x']"`)
- [ ] Action `view_mode="list,form"` (not `"tree,form"`)
- [ ] Inheritance uses `<xpath>` or `<field name="..." position="...">`, not duplicated views
- [ ] No groups-only buttons without server-side check
- [ ] Form fields with `readonly=` use direct expressions

## Frontend checklist (if JS present)

- [ ] `/** @odoo-module **/` at top of every JS file
- [ ] `patch(target, {...})` signature (no name argument)
- [ ] `super.method(...)` (not `_super(...)`)
- [ ] Imports from `@web/...` (not `web.*`)
- [ ] Asset bundle declared in manifest
- [ ] OWL components use static `template` and static `props`

## Testing checklist

- [ ] At least one test per public method
- [ ] Tests use `@tagged("post_install", "-at_install")`
- [ ] No `print()` / `breakpoint()` in tests
- [ ] No skipped tests without comment
- [ ] Test class names start with `Test`

## QWeb / reports checklist

- [ ] `t-out` preferred over `t-esc`
- [ ] `t-field` for typed field rendering
- [ ] No `t-raw` (security)
- [ ] Templates wrapped in `web.html_container` and (typically) `web.external_layout`
- [ ] `report_name` matches template's external ID

## Performance smell tests

- [ ] No unstored computes used in `_order` or domains
- [ ] FK and selection fields used in domains have `index=True`
- [ ] No `mapped("rel.field.subfield")` over potentially huge recordsets without bounds

## Output format

Group findings by severity:

**🔴 Blockers** (security, correctness, prod-breaking)
**🟡 Issues** (best-practice violations, performance smells)
**🟢 Nits** (style, naming, polish)

Cite the file and line. Suggest the fix in code where possible.

End with a summary: "X blockers, Y issues, Z nits. Top 3 priorities to fix:"
