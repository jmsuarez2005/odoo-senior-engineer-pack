---
name: odoo-add-view
description: Generate an Odoo 17 view (form, list, kanban, search, graph, pivot, calendar, gantt, activity) for a model
argument-hint: <model> <view_type> [--inherit=<existing_view_xml_id>]
---

You are creating a v17 view for a model. Follow `views-and-actions` skill conventions, including v17-specific syntax (`<list>` not `<tree>`, direct attribute expressions, no `attrs=`).

## Inputs

`$ARGUMENTS` — `<model>` and `<view_type>`.

If absent, ask:
1. Which model
2. Which view type
3. New view or inheriting an existing one?
4. Where in the file structure should the view live (`views/<model_snake>_views.xml`)?

## Steps

1. Locate or create `views/<model_snake>_views.xml`. If it exists, open it; otherwise create it (with the standard XML wrapper).

2. Generate the view record according to the type:
   - **form**: `<header>` (statusbar buttons + `<field name="state" widget="statusbar"/>`), `<sheet>` (oe_button_box, oe_title, `<group>`/`<group>`, `<notebook>` with pages), chatter at the bottom if model has `mail.thread`.
   - **list**: `<list string="...">` with the most important columns, `decoration-*` for visual cues, `optional="show|hide"` for less-important fields, `groups="..."` for company-only fields.
   - **kanban**: `<kanban default_group_by="state">` with template, mobile-friendly card.
   - **search**: search fields, common filters, group-by group.
   - **graph / pivot**: declare measures and dimensions.
   - **calendar**: date_start, date_stop, color, mode.
   - **gantt** (Enterprise): date_start, date_stop, color.
   - **activity**: standard for `mail.activity.mixin` models.

3. Generate the matching `ir.actions.act_window` (only if creating a new view set, not for inherited views):
   - `view_mode="list,form"` (or whatever combination is appropriate)
   - Helpful `help` text
   - `context=` with sensible default filters

4. For inherited views: use `<xpath expr="..." position="...">` or `<field name="..." position="after|before|inside|attributes|replace">`. Match by field name when possible, by attribute when not.

5. Add the new view file to the manifest's `data` list.

6. Add or update a menu item if the action is new.

## Quality bar

- v17 syntax: `<list>`, no `attrs=`, no `states=`, direct expressions for `readonly`/`invisible`/`required`.
- Decoration classes from Bootstrap 5: `text-bg-success`, `text-bg-danger`, etc.
- `optional="show"` / `optional="hide"` on list fields the user can toggle.
- `widget="..."` chosen consciously: `statusbar`, `badge`, `boolean_toggle`, `monetary`, `image`, etc.
- Chatter block (`<div class="oe_chatter">`) only on models that inherit `mail.thread`.
- Search view: filters use `domain="[...]"`; group-by uses `context="{'group_by': 'field'}"`.

## What NOT to do

- Don't generate a `<tree>` view in v17. Use `<list>`.
- Don't use `attrs="{...}"`. Use direct attribute expressions.
- Don't include every field on a list view — pick the 5-7 most useful and `optional="show"` the rest.
- Don't add a chatter block to a model that doesn't inherit `mail.thread` — silent emptiness.
- Don't hardcode style colors — use Bootstrap 5 utility classes.
