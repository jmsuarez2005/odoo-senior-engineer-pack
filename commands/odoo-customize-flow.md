---
name: odoo-customize-flow
description: Plan a customization to a standard Odoo flow — sale order, purchase order, manufacturing order, project task, helpdesk ticket. Identify safe extension points and produce the changes needed.
argument-hint: <flow> <change_description>
---

You are planning a customization to an existing Odoo flow. Goal: produce a **safe, upgrade-friendly** change plan.

## Inputs

`$ARGUMENTS` — the flow (`sale-order`, `purchase-order`, `mrp-order`, `project-task`, `helpdesk-ticket`, etc.) and a description of the desired change.

If unclear, ask:
1. Which standard model is the entry point?
2. What event triggers the customization? (create, write, state change, button click)
3. What's the desired behavior?
4. Who can do it / who can't? (groups, multi-company, multi-website)
5. What stays standard vs becomes custom?

## Steps

1. Identify the standard flow's **extension points**:
   - State transitions (`action_confirm`, `_post`, `button_validate`)
   - Hooks (`@api.model_create_multi`, `_compute_*`, `_action_*`)
   - Selection extension via `selection_add` (states, types)
   - Inheriting views with xpath
   - Server actions via `binding_model_id`

2. For the requested change, pick the **least invasive** extension point.

3. Identify **side effects** the change might have on:
   - Reports (do report templates reference fields you're removing/renaming?)
   - Other modules (does `sale_timesheet` or `mrp` rely on this exact transition?)
   - Standard tests (will they still pass?)
   - Migration paths (is this safe to upgrade later?)

4. Produce the change plan.

## Output

```markdown
## Customization plan: <flow> — <change>

### Standard flow today
<Diagram or step list of how it works without customization>

### Desired change
<Concise statement>

### Extension point chosen
<Method/hook/view, with justification>

### Files to create / modify
- `models/<model>.py` — extend with `_inherit`
- `views/<model>_views.xml` — view inheritance
- `security/ir.model.access.csv` — if adding new groups
- `tests/test_<flow>.py` — tests for the new behavior

### Code (the actual changes)
<Show the inherits, with comments explaining why each piece is there>

### Side effects to verify
- [ ] Standard report still renders (check fields used)
- [ ] `sale_timesheet` (or whichever) integration still works
- [ ] Multi-company / multi-website still respected
- [ ] Migration script if stored fields change

### Tests to add
| Test | What it asserts |
|---|---|

### Alternative approaches considered
<Brief: why the chosen approach beats others>

### Upgrade risk
<Assess: low / medium / high. Why?>
```

## Quality bar

- Use the **least invasive** point. Inheriting `action_confirm` is better than overriding `write`.
- Always preserve `super()` calls. Never replace standard behavior unconditionally.
- Use `selection_add` (with `ondelete`) for state extensions, not `selection=`.
- Add tests for both the new behavior AND the standard path (so refactoring keeps both).
- Identify the upgrade path: what happens when client upgrades to v18?

## What NOT to do

- Don't skip the side-effects analysis.
- Don't override `write()` if `_compute_*` or `@api.depends` would do.
- Don't change standard model field types or remove standard fields.
- Don't propose patching standard module code directly — always inherit.
- Don't add `_inherit` and forget to add the new file to `__init__.py`.
