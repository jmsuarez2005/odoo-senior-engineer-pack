---
name: orm-models
description: Define Odoo 17 models, fields, decorators, and recordset operations. Use when creating or extending models, working with computed/related/stored fields, inheritance (_inherit, _inherits, abstract), recordsets, environment, or @api decorators.
---

# ORM & Models (Odoo 17)

## When to use this skill

Anything involving `models.Model`, `models.TransientModel`, `models.AbstractModel`, fields, recordsets, or the `@api.*` decorator family.

## Model declaration

```python
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class HrOvertime(models.Model):
    _name = "hr.overtime"
    _description = "Employee Overtime"             # required, lints fail without it
    _inherit = ["mail.thread", "mail.activity.mixin"]   # mixins for chatter
    _order = "date desc, id desc"                  # default ORDER BY
    _rec_name = "name"                             # default name field (defaults to "name" if absent)
    _check_company_auto = True                     # auto-validate company_id consistency

    name = fields.Char(string="Reference", required=True, copy=False, default="New", tracking=True)
    employee_id = fields.Many2one("hr.employee", required=True, tracking=True, index=True)
    date = fields.Date(default=fields.Date.context_today, required=True)
    hours = fields.Float(digits=(4, 2), required=True)
    state = fields.Selection(
        [("draft", "Draft"), ("submitted", "Submitted"), ("approved", "Approved"), ("refused", "Refused")],
        default="draft",
        tracking=True,
        required=True,
        copy=False,
    )
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company, index=True
    )

    _sql_constraints = [
        ("hours_positive", "CHECK(hours > 0)", "Overtime hours must be positive."),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("hr.overtime") or "New"
        return super().create(vals_list)
```

## Field types — the ones that matter

### Scalars
- `Char(size=N)` — never set `size` unless you have a real DB-level reason. UI length is a view concern.
- `Text` — multi-line plain text.
- `Html(sanitize=True, sanitize_attributes=True)` — sanitize defaults are correct; turning them off is a security decision.
- `Integer`, `Float(digits=(precision, scale))` — `digits` controls UI rounding via `decimal.precision`.
- `Monetary(currency_field="currency_id")` — **always** specify `currency_field`. Required.
- `Date` (no time, no timezone), `Datetime` (UTC in DB, displayed in user TZ), `Boolean`.
- `Selection([(key, label), ...])` — keys must be stable (used in domains, code).
- `Json` — for unstructured data; not searchable.
- `Properties(definition_record=..., definition_record_field=...)` — v17 dynamic fields.

### Relational
- `Many2one("model", ondelete="restrict|cascade|set null")` — explicitly choose `ondelete`. Default is `set null` for non-required, `restrict` for required.
- `One2many("model", "inverse_field_name")` — **requires** the inverse `Many2one`. No inverse = nothing works.
- `Many2many("model", relation="rel_table", column1="x_id", column2="y_id")` — name `relation` explicitly when both sides have m2ms to the same model, else collisions.
- `Reference([(model, label), ...])` — polymorphic foreign key. Heavier than Many2one; use only when needed.

### Pseudo-fields
- `Binary(attachment=True)` — store as `ir.attachment` (recommended) vs inline in column.
- `Image(max_width=1920, max_height=1920)` — auto-resize wrapper around `Binary`.

## Computed and related fields

```python
# Pure compute (not stored)
total = fields.Float(compute="_compute_total")

@api.depends("line_ids.price_unit", "line_ids.quantity")
def _compute_total(self):
    for record in self:
        record.total = sum(line.price_unit * line.quantity for line in record.line_ids)
```

```python
# Stored compute (search/order/group OK, costs DB writes)
total = fields.Float(compute="_compute_total", store=True)
```

```python
# Related (shortcut to a chain — auto-stored if all hops are stored)
partner_email = fields.Char(related="partner_id.email", readonly=True)
```

```python
# Editable computed (rare, but useful for "default that user can override")
amount = fields.Float(compute="_compute_amount", store=True, readonly=False)
```

### Compute rules

- `@api.depends(...)` is **mandatory** for computed fields (else it's recomputed every read).
- Always loop with `for record in self:` — `self` is a recordset, not a single record.
- Set the field on **every** record in `self` — missing assignment leaves stale values and breaks tests.
- For computed Many2one/One2many/Many2many, depend on the right keys (the FK on the *child*, not just the parent's o2m).
- Use `@api.depends_context("foo")` when the result depends on `self.env.context`.

## Decorators

| Decorator | Purpose | Notes |
|---|---|---|
| `@api.depends(*fields)` | Trigger recompute | Required on computed |
| `@api.depends_context(*keys)` | Recompute when context key changes | For context-sensitive computes |
| `@api.constrains(*fields)` | Validate after write | Raise `ValidationError` |
| `@api.onchange(*fields)` | UI-only, returns warning/domain | NOT triggered by RPC writes |
| `@api.model` | Class-level (no record) | `self` is empty recordset |
| `@api.model_create_multi` | Batch-aware create | **Use this in v17, not `@api.model` on `create`** |
| `@api.ondelete(at_uninstall=False)` | Hook on unlink | Replaces overriding `unlink` for guards |
| `@api.returns("res.partner")` | Decorator over old API | Rare, for backwards compat |

## Inheritance

### Classical extension
```python
class ResPartner(models.Model):
    _inherit = "res.partner"  # extends the existing res.partner

    overtime_count = fields.Integer(compute="_compute_overtime_count")
```

### Prototype + new model
```python
class HrOvertimeRequest(models.Model):
    _name = "hr.overtime.request"
    _inherit = "mail.thread"   # absorbs mail.thread's fields/methods
    _description = "Overtime Request"
```

### Delegation (`_inherits`) — usually wrong
```python
class HrEmployeeBadge(models.Model):
    _name = "hr.employee.badge"
    _inherits = {"hr.employee": "employee_id"}  # auto-creates the partner-style delegation
    employee_id = fields.Many2one("hr.employee", required=True, ondelete="cascade")
```
Only use when you really want "is-a-but-also-has-its-own-table" semantics. 99% of the time you want classical or prototype inheritance.

### Abstract
```python
class MyMixin(models.AbstractModel):
    _name = "my.mixin"
    _description = "My mixin"

    description = fields.Text()

    def shared_method(self):
        ...
```

## Recordsets — the mental model

A recordset is a **set** of records of the same model. `self` is always a recordset; never assume singleton without `ensure_one()`.

```python
records = self.env["hr.overtime"].search([("state", "=", "draft")])
records  # recordset of N records

records[0]                 # first record (still a recordset of size 1)
records.ids                # list of integer IDs
len(records)               # N
records.filtered("active") # records where active is truthy
records.filtered(lambda r: r.hours > 8)
records.filtered_domain([("hours", ">", 8)])
records.mapped("name")     # list (or recordset for relational fields)
records.mapped("employee_id")  # recordset of all referenced employees
records.sorted(key="date", reverse=True)
records1 | records2        # union
records1 & records2        # intersection
records1 - records2        # difference
records.ensure_one()       # raise if size != 1
```

## Environment

```python
self.env.user                  # res.users record for the current user
self.env.company               # active company (multi-company aware)
self.env.companies             # all allowed companies
self.env.context               # frozendict — never mutate
self.env.cr                    # raw cursor (use sparingly)
self.env.ref("module.xml_id")  # fetch by external ID

records.with_context(active_test=False)   # bypass active=False filter
records.with_user(other_user)             # eval ACL/rules as that user
records.with_company(other_company)       # set active company
records.sudo()                            # bypass ACL/rules — DANGEROUS, document why
records.flush_recordset()                 # force pending writes to DB
records.invalidate_recordset(["field"])   # drop cache for fields
```

## Raw SQL

Sometimes necessary. Always parameterized:

```python
self.env.cr.execute(
    "SELECT id, name FROM res_partner WHERE email = %s AND active",
    (email,),  # tuple, even for one parameter
)
rows = self.env.cr.fetchall()
```

Never:
```python
# WRONG — SQL injection
self.env.cr.execute(f"SELECT * FROM res_partner WHERE email = '{email}'")
```

After raw `INSERT/UPDATE/DELETE`, you're bypassing the ORM cache. Call `invalidate_model` or restart the affected operation through the ORM instead.

## Common pitfalls

- Forgetting `@api.model_create_multi` and overriding `create(self, vals)` — works, but breaks batch creates and is the v17 anti-pattern.
- Computing without `@api.depends` — silently recomputed on every read, killing performance.
- Setting only the "interesting" record's field in compute, leaving others undefined — TypeError on read.
- Using `@api.onchange` for validation — bypassed by RPC writes. Use `@api.constrains`.
- Using `lambda self: ...` as default with `self` referring to the wrong env — `default=lambda self: self.env.user` is fine, but capturing `self` from a wider scope is not.
- Missing `ensure_one()` before accessing fields when you assumed a singleton.
- Mutating `self.env.context` directly — it's a frozendict; use `with_context(**new)`.

## References

- [Odoo 17 — ORM Reference](https://www.odoo.com/documentation/17.0/developer/reference/backend/orm.html)
- [Odoo 17 — Fields](https://www.odoo.com/documentation/17.0/developer/reference/backend/orm.html#fields)
- [Odoo 17 — Inheritance](https://www.odoo.com/documentation/17.0/developer/reference/backend/orm.html#inheritance-and-extension)
