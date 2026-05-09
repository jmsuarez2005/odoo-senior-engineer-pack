---
name: odoo-add-field
description: Add a field to an Odoo 17 model with all the boilerplate (Python definition, view exposure, security implications, test)
argument-hint: <model> <field_name> [--type=Char] [--label="..."] [--required] [--tracking]
---

You are adding a field to an Odoo 17 model with senior-grade attention to the side effects.

## Inputs

`$ARGUMENTS` — at minimum: `<model>` (e.g. `hr.overtime`) and `<field_name>` (snake_case).

If anything's missing, ask:
1. Field type (`Char`, `Text`, `Boolean`, `Integer`, `Float`, `Date`, `Datetime`, `Selection`, `Many2one`, `One2many`, `Many2many`, `Monetary`, `Html`, `Binary`, `Image`)
2. Label (string=)
3. Required? Default value?
4. Tracking? (only meaningful if model inherits `mail.thread`)
5. Computed or stored?
6. Indexed?
7. Multi-company sensitive? (i.e. should it be tied to `company_id`)

## Steps

1. Locate the Python file for the model (`models/<model_snake>.py`). If extending another module's model, ensure the file is using `_inherit = "..."`.

2. Add the field with:
   - Correct type and constructor args
   - `string=` (label) only if it differs from the auto-generated one
   - `required=`, `default=`, `tracking=` if specified
   - `index=True` if the user said it'll be queried/sorted/grouped
   - `currency_field=` for `Monetary` (mandatory)
   - `inverse_name` for `One2many`
   - `relation`, `column1`, `column2` for `Many2many` only when needed
   - `ondelete=` for `Many2one` if not the default `restrict`/`set null`
   - Docstring (single line) if non-obvious

3. If the field is computed, add the `_compute_<name>` method:
   - `@api.depends(...)` with the right deps
   - Loop `for record in self:`
   - Set the field on **every** record

4. Add the field to the relevant views:
   - Form view: in the appropriate `<group>` or `<page>`
   - List view: only if it makes sense as a column (small enough, frequently relevant)
   - Search view: if users will filter by it
   - Use direct expression syntax for `readonly`/`invisible`/`required` (no `attrs`)

5. Update security if needed:
   - If the field exposes sensitive data, consider whether existing record rules cover it.
   - If the field references a multi-company model, consider `check_company=True`.

6. Add a test:
   - Create a record with the new field set
   - Read it back
   - If computed, write to deps and assert the recompute
   - If required, assert that omitting raises

7. If the field is **stored** and added to an existing model with existing rows, write a `migrations/17.0.X.Y.Z/post-migration.py` to backfill values.

8. Bump the module version (patch level for new field on existing model: `17.0.1.0.0` → `17.0.1.0.1`; minor if it's a new feature surface: `→ 17.0.1.1.0`).

## Output

For each file touched: show the diff (or the new file content if creating).

End with:
- Summary of files changed
- Reminder about migration script if backfill needed
- Reminder to bump version (already done if you did it)

## What NOT to do

- Don't add a Selection field with `[(0, 'Zero'), (1, 'One')]` (numeric keys) — they make domains awkward; use string keys.
- Don't add a stored compute without `@api.depends` — silent breakage.
- Don't add a `Many2one` to a multi-company model without thinking through `check_company`.
- Don't add a field to the list view that's expensive to render (HTML, large Text).
- Don't forget the migration script for existing data when adding required+stored fields.
