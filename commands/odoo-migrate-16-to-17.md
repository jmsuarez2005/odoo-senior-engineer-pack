---
name: odoo-migrate-16-to-17
description: Analyze a v16 Odoo module and produce a migration plan to v17
---

You are producing a migration plan from Odoo 16 to Odoo 17 for a specific module.

## Inputs

`$ARGUMENTS` — module path or name. If absent, ask which module.

## Steps

1. Use the `migration-16-to-17` skill as your reference of breaking changes.

2. Scan the module for migration triggers:
   - **Manifest**: version starts with `16.0.`, deps include any v16-only modules.
   - **Views**: `<tree>` tags, `attrs="..."`, `states="..."`, `view_mode` containing `tree`.
   - **ORM**: `@api.model\ndef create(self, vals)`, `name_get(self)`, `_inherit` with v16-only models.
   - **JS**: `patch(target, "name", {...})` signature, `_super(`, `web.field_registry`, `web.core`, `tag="owl"`.
   - **QWeb**: heavy use of `t-esc` (acceptable but `t-out` is preferred).

3. For each finding, classify:
   - **Mechanical**: can be done with sed / regex (e.g. `<tree>` → `<list>`)
   - **Semi-mechanical**: needs careful translation (e.g. `attrs` → expression)
   - **Manual**: needs design thinking (e.g. removed mixin, restructured API)

4. Estimate effort:
   - **S** (< 30 min)
   - **M** (1-3 hours)
   - **L** (a day or more, may need design review)

## Output

Produce a migration plan with:

### Summary
- Total findings, breakdown by classification
- Estimated total effort
- Top risks (things that might break behavior, not just compile)

### Findings table

| File | Line | Issue | Type | Effort | Fix |
|---|---|---|---|---|---|
| views/foo.xml | 42 | `<tree>` tag | Mechanical | S | `<list>` |
| views/foo.xml | 67 | `attrs="{'readonly': [('state','=','done')]}"` | Semi-mechanical | S | `readonly="state == 'done'"` |
| models/foo.py | 89 | `@api.model\ndef create(self, vals)` | Semi-mechanical | M | `@api.model_create_multi`, accept `vals_list`, loop |
| static/src/js/foo.js | 12 | `patch(X, "name", {...})` | Mechanical | S | drop the name |

### Step-by-step plan

1. Create branch `17.0` from `16.0`.
2. Bump manifest version to `17.0.1.0.0`.
3. Run mechanical fixes (provide a sed script).
4. Manual fixes (list them with file:line).
5. Test install on v17.
6. Test upgrade from v16 DB copy.
7. Run pylint-odoo against v17.

### Sed script for mechanical fixes
```bash
# Adjust paths to your module
find . -name "*.xml" -exec sed -i 's|<tree |<list |g; s|</tree>|</list>|g' {} +
find . -name "*.xml" -exec sed -i 's|view_mode">tree|view_mode">list|g' {} +
```

(Don't auto-run this — show it to the user; they decide when to apply.)

### Risks called out
- Specific spots where v17 behavior subtly differs (e.g., `_compute_display_name` ordering) and the user should test specifically.

## What NOT to do

- Don't actually edit files — produce the plan first. Editing can come as a follow-up.
- Don't promise zero-effort migration — there's always at least testing.
- Don't suggest using `<tree>` shim "just for now" — clean migrations are non-negotiable.
