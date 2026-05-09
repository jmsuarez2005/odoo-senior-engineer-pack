# Odoo 16 → 17 Migration Deltas (concise)

## Views (most modules hit these)

```diff
- <tree string="...">
+ <list string="...">

- <field name="x" attrs="{'readonly': [('state', '!=', 'draft')]}"/>
+ <field name="x" readonly="state != 'draft'"/>

- <button name="approve" states="submitted"/>
+ <button name="approve" invisible="state != 'submitted'"/>

- <field name="view_mode">tree,form</field>
+ <field name="view_mode">list,form</field>
```

## Domain → expression conversion

| v16 attrs domain | v17 expression |
|---|---|
| `[('state', '=', 'X')]` | `state == 'X'` |
| `[('state', '!=', 'X')]` | `state != 'X'` |
| `[('field', 'in', ['a', 'b'])]` | `field in ['a', 'b']` |
| `[('a', '=', 1), ('b', '=', 2)]` | `a == 1 and b == 2` |
| `['|', ('a', '=', 1), ('b', '=', 2)]` | `a == 1 or b == 2` |
| `[('field', '=', False)]` | `not field` |

## ORM

```diff
- @api.model
- def create(self, vals):
+ @api.model_create_multi
+ def create(self, vals_list):

- def name_get(self):
-     return [(r.id, r.code + " - " + r.name) for r in self]
+ display_name = fields.Char(compute="_compute_display_name", store=True)
+ @api.depends("code", "name")
+ def _compute_display_name(self):
+     for r in self:
+         r.display_name = f"{r.code} - {r.name}"
```

## JavaScript

```diff
- patch(MyComponent.prototype, "module.MyComponent", {
+ patch(MyComponent.prototype, {

- this._super(...arguments);
+ super.setup(...arguments);

- import fieldRegistry from "web.field_registry";
- fieldRegistry.add("my_widget", MyWidget);
+ import { registry } from "@web/core/registry";
+ registry.category("fields").add("my_widget", { component: MyWidget, supportedTypes: ["char"] });
```

## Mechanical sed pass (review before applying)

```bash
# Views
find . -name "*.xml" -exec sed -i 's|<tree |<list |g; s|<tree>|<list>|g; s|</tree>|</list>|g' {} +
find . -name "*.xml" -exec sed -i 's|view_mode">tree|view_mode">list|g' {} +

# JS — drop the patch name (manual review needed for each)
# rg "patch\([^,]+,\s*\"[^\"]+\"," --type=js
```

For `attrs=` and `states=`, there's no safe automated rewrite — the expressions need human translation.
