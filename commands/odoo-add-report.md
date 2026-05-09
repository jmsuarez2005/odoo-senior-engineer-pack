---
name: odoo-add-report
description: Scaffold a QWeb PDF report for an Odoo 17 model with paperformat, action, and template
argument-hint: <model> [--name="..."]
---

You are scaffolding a complete QWeb PDF report. Follow the `qweb-reports` skill.

## Inputs

`$ARGUMENTS` — `<model>` (e.g. `hr.overtime`).

If absent, ask:
1. Which model
2. Report display name (e.g. "Overtime Slip")
3. Page format (A4 / Letter; default A4)
4. Orientation (Portrait / Landscape; default Portrait)
5. Should the report appear in the model's Print menu? (default: yes)

## Steps

1. Create or extend `reports/<model_snake>_report.xml` with the report action and paperformat.

2. Create `reports/<model_snake>_report_template.xml` with a starter QWeb template:
   - Wrapped in `web.html_container`
   - Uses `web.external_layout` (so it picks up company branding)
   - Has a `<t t-foreach="docs" t-as="o">` loop
   - Includes name, key fields, a table for line items if applicable, signature/approval area, page-friendly structure

3. Update `__init__.py` in `reports/` to import any Python file (only needed if there's compute logic — many reports don't need Python).

4. Add both XML files to the manifest's `data` list.

5. (Optional) Generate a `models/report_<model>.py` with `_compute_*` helpers if the report needs prepared data — but only if necessary; prefer computing in QWeb when simple.

## Output

Produce the `<record id="action_report_*">`, the `<record id="paperformat_*">`, and the `<template id="report_*_template">`.

Use these conventions for IDs:
- `action_report_<model_snake>` — the report action
- `paperformat_<model_snake>` — the paperformat (only if customizing from default)
- `report_<model_snake>_template` — the QWeb template

## Quality bar

- `t-out` instead of `t-esc` for safe values
- `t-field` for typed field rendering with widget options (`monetary`, `date`, etc.)
- No inline `<style>` (use Bootstrap 5 utility classes)
- Tables have `<thead>` so headers repeat across pages
- All user-facing strings wrapped with `_()` for translation
- Report works for both 1 record (button) and N records (batch print)

## What NOT to do

- Don't use `t-raw` (security risk).
- Don't hardcode the company logo — `web.external_layout` handles it.
- Don't generate an empty `paperformat` if the default is fine — just reference `web.paperformat_euro` or `web.paperformat_us`.
- Don't put DB writes in the QWeb template — templates are render-only.
