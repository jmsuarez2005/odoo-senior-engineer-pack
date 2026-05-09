---
name: migration-16-to-17
description: Migrate an Odoo 16 module to Odoo 17 — breaking changes, deprecations, view renames, OWL changes, manifest tweaks. Use when porting modules from v16 to v17 or reviewing v16 code for v17 compatibility.
---

# Migration: Odoo 16 → 17

## When to use this skill

You have a module that works on Odoo 16 and need it to work on Odoo 17. Or you're reviewing v16 code for issues that v17 will surface.

## The big picture

Odoo 17 is **not** as breaking as 14→15 or 15→16. Most modules port over with manageable changes. The biggest categories:

1. **Views**: `<tree>` → `<list>`, `attrs="{...}"` and `states=` removed in favor of direct attribute expressions
2. **Frontend**: OWL 2 (already in v16) — but JS module imports cleaned up; some patches changed signature
3. **ORM**: `_inherit` + name change pattern unchanged; some method signatures cleaned up
4. **Manifest**: minor (`assets` declarations stable)
5. **Removed mixins/fields**: a few legacy ones gone

## The view changes (most modules will hit these)

### `<tree>` → `<list>`

```xml
<!-- v16 -->
<tree string="Records">
    <field name="name"/>
</tree>

<!-- v17 -->
<list string="Records">
    <field name="name"/>
</list>
```

Old XML still loads in v17 via a compatibility shim, but pylint-odoo and OCA CI will reject it. Migrate.

### `attrs` and `states` are gone

```xml
<!-- v16 -->
<field name="hours" attrs="{'readonly': [('state', '!=', 'draft')], 'invisible': [('approved', '=', False)]}"/>
<button name="action_approve" states="submitted"/>

<!-- v17 -->
<field name="hours" readonly="state != 'draft'" invisible="not approved"/>
<button name="action_approve" invisible="state != 'submitted'"/>
```

The new syntax is **Python-like expressions** evaluated against the record's fields. No more domain tuple lists.

Conversion rules:
- `[('state', '=', 'X')]` → `state == 'X'`
- `[('state', '!=', 'X')]` → `state != 'X'`
- `[('field', 'in', ['a', 'b'])]` → `field in ['a', 'b']`
- `[('a', '=', 1), ('b', '=', 2)]` (implicit AND) → `a == 1 and b == 2`
- `['|', ('a', '=', 1), ('b', '=', 2)]` (explicit OR) → `a == 1 or b == 2`
- `[('field', '=', False)]` → `not field`

The `states="..."` shortcut for buttons becomes `invisible="state not in ['x', 'y']"` (note the inversion).

### Action `view_mode` references

```xml
<!-- v16 -->
<field name="view_mode">tree,form</field>

<!-- v17 -->
<field name="view_mode">list,form</field>
```

## ORM changes

### `@api.model` on `create` is the v15 way; `@api.model_create_multi` is the v17 way

Already true in v16, but more strictly enforced in v17:

```python
# AVOID
@api.model
def create(self, vals):
    ...

# CORRECT
@api.model_create_multi
def create(self, vals_list):
    for vals in vals_list:
        ...
    return super().create(vals_list)
```

### `name_get` is deprecated in favor of `_compute_display_name`

```python
# v16 way
def name_get(self):
    result = []
    for record in self:
        name = f"{record.code} - {record.name}"
        result.append((record.id, name))
    return result

# v17 way
display_name = fields.Char(compute="_compute_display_name", store=True)

@api.depends("code", "name")
def _compute_display_name(self):
    for record in self:
        record.display_name = f"{record.code} - {record.name}"
```

`name_get` still works (compatibility) but new code should use computed `display_name`.

### `_search` overrides — signature matters

If you override `_search` for custom search behavior, double-check the signature against v17's reference (the v17 `_search` is typed and stricter about returning a Query/SQL).

## Frontend / OWL changes

### `patch()` no longer takes a name

```js
// v16
patch(MyComponent.prototype, "my.module.MyComponent", {
    setup() {
        this._super(...arguments);
        // ...
    },
});

// v17
patch(MyComponent.prototype, {
    setup() {
        super.setup();
        // ...
    },
});
```

Note: `this._super(...arguments)` → `super.method(...arguments)`. Standard ES6 super.

### Field widget registration

```js
// v16
import fieldRegistry from "web.field_registry";
fieldRegistry.add("my_widget", MyWidget);

// v17
import { registry } from "@web/core/registry";
registry.category("fields").add("my_widget", {
    component: MyWidget,
    supportedTypes: ["char"],
});
```

The registry entries are now objects with metadata, not bare components.

### Imports cleanup

Many `web.*` imports moved to `@web/...`. Common conversions:

| v16 import | v17 import |
|---|---|
| `web.core` | `@web/core/*` (more granular) |
| `web.field_registry` | `@web/core/registry` |
| `web.utils` | `@web/core/utils/*` |
| `web.session` | `@web/core/session` |
| `web.AbstractAction` | Use a Component + register in `actions` category |

When in doubt, search the v17 source under `addons/web/static/src/` for the new path.

### OWL 1 → OWL 2 (mostly done in v16, but verify)

If your module still has any of these, fix them:
- `tags = "owl"` on a Widget — replace with a real OWL Component class.
- `useState({...})` outside `setup()` — must be inside `setup()`.
- `xml/template_id` references where the template wasn't bundled.

## Manifest changes

Mostly stable. Things to verify:

- **Version prefix**: bump from `16.0.X.Y.Z` to `17.0.X.Y.Z`. Reset minor/patch if you want a clean v17.0 line, or carry your numbering forward.
- **Assets globs**: stable. The `web.assets_backend` / `web.assets_frontend` / `web.assets_tests` keys unchanged.
- **`depends`**: remove deps on modules that no longer exist in v17 (rare; check the v17 addon list). A few enterprise-only modules were renamed/merged.

## Removed / renamed things to grep for

- `attrs="..."` — should be 0 occurrences in v17 code
- `states="..."` (on buttons) — should be 0 occurrences
- `<tree>` — replace with `<list>`
- `name_get` (defining new ones) — use `_compute_display_name`
- `_super(...)` (in JS patches) — use `super.method(...)`
- `web.field_registry` (JS imports) — use `@web/core/registry`
- `tag="owl"` (in old Widget definitions) — use Component
- `t-esc` in QWeb reports — prefer `t-out` (semantically equivalent for safe values, but `t-out` is the v17 canonical name)

## Migration playbook

For a single module, in order:

1. **Branch** — `git checkout -b 17.0` from your v16 branch.
2. **Manifest** — bump version to `17.0.X.Y.Z`, drop unused deps.
3. **Views** — `sed -i 's/<tree/<list/g; s/<\/tree>/<\/list>/g' views/*.xml`, then convert `attrs`/`states` (no automated tool — read each one, write the expression). Update `view_mode` strings in actions.
4. **ORM** — convert any `@api.model` `create(self, vals)` to `@api.model_create_multi` + `vals_list`. Convert `name_get` to `_compute_display_name` if touched.
5. **JS** — fix `patch` signatures, registry imports, `super` calls.
6. **Test install** — `odoo -d test17 -i your_module --test-enable --stop-after-init`. Read every traceback.
7. **Test upgrade** — make a copy of a v16 production DB, then `odoo -d copy16 --upgrade-path=...` (or use OpenUpgrade).
8. **Run pylint-odoo** on v17 — catches deprecated patterns.
9. **Manual smoke test** — open every list, form, kanban; click every button; print every report.

## Stored field migrations

If you renamed or removed a stored field, write a `migrations/17.0.X.Y.Z/` script:

```python
# my_module/migrations/17.0.1.0.0/pre-migration.py
def migrate(cr, version):
    # Rename a column
    cr.execute("""
        ALTER TABLE hr_overtime
        RENAME COLUMN old_name TO new_name
    """)
```

Or `post-migration.py` for things needing the upgraded ORM:

```python
# post-migration.py
from odoo import api, SUPERUSER_ID

def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    records = env["hr.overtime"].search([])
    for r in records:
        r.new_field = some_compute(r)
```

Migration scripts run **on upgrade**, not on fresh install. Always test against a copy of production.

## OpenUpgrade

For migrating production databases (not just module code), use [OCA OpenUpgrade](https://github.com/OCA/OpenUpgrade). It's a fork of Odoo with migration scripts for every standard module, version-by-version.

```bash
# Approach: clone OpenUpgrade, run upgrade against a v16 DB to get a v17 DB
git clone -b 17.0 https://github.com/OCA/OpenUpgrade.git
./openupgrade-bin -d my_v16_db --update=all --stop-after-init
```

For OCA modules, there's usually an OpenUpgrade-compatible version available.

## Common pitfalls

- Forgot to convert `attrs="{'invisible': ...}"` — view loads in v17 (compatibility) but raises a deprecation warning; pylint-odoo will flag it.
- Buttons with `states="submitted"` — same, deprecated, fix to `invisible="state != 'submitted'"`.
- `view_mode="tree,form"` in actions — list view doesn't open with that string in v17. Change to `"list,form"`.
- `patch()` with name argument left in — silent breakage; the function signature changed, you'll get a runtime error.
- Forgetting `super().` in OWL 2 patches — calls the wrong parent method.
- Using `name_get` AND `display_name` compute simultaneously — `display_name` wins; remove `name_get`.
- A module that imports from `@web/legacy/...` in v17 — those paths shrunk; many things moved out of `legacy`.

## References

- [Odoo 17 release notes](https://www.odoo.com/odoo-17-release-notes)
- [Odoo 17 — Upgrade documentation](https://www.odoo.com/documentation/17.0/administration/upgrade.html)
- [OCA OpenUpgrade](https://github.com/OCA/OpenUpgrade)
- [OCA migration guides](https://github.com/OCA/maintainer-tools/wiki/Migration)
