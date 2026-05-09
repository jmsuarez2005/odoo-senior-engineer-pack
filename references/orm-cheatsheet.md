# Odoo 17 — ORM Cheatsheet

Quick-reference card. For depth, read `skills/orm-models/SKILL.md`.

## Field reference (one-liners)

```python
# Char / Text
name = fields.Char(required=True, index=True, default="X", copy=False)
description = fields.Text()
notes = fields.Html(sanitize=True)

# Numbers
qty = fields.Integer(default=0)
price = fields.Float(digits=(12, 2))
amount = fields.Monetary(currency_field="currency_id")

# Dates
start_date = fields.Date(default=fields.Date.context_today)
end_dt = fields.Datetime(default=fields.Datetime.now)

# Boolean / Selection
active = fields.Boolean(default=True)
state = fields.Selection([("a", "A"), ("b", "B")], default="a", required=True, index=True)

# Relational
partner_id = fields.Many2one("res.partner", required=True, ondelete="restrict", index=True)
line_ids = fields.One2many("sale.order.line", "order_id")
tag_ids = fields.Many2many("res.partner.tag")

# Special
image = fields.Image(max_width=1024, max_height=1024)
attachment = fields.Binary(attachment=True)
data = fields.Json()
```

## Decorators

```python
@api.depends("a", "b.c")
def _compute_x(self):
    for r in self:
        r.x = r.a + sum(r.b.mapped("c"))

@api.constrains("hours")
def _check_hours(self):
    for r in self:
        if r.hours < 0:
            raise ValidationError(_("..."))

@api.onchange("partner_id")            # UI-only, not RPC-triggered
def _onchange_partner(self):
    if self.partner_id:
        self.email = self.partner_id.email

@api.model_create_multi                 # use this in v17, not @api.model
def create(self, vals_list):
    return super().create(vals_list)

@api.ondelete(at_uninstall=False)       # v15+, replaces unlink override
def _check_can_delete(self):
    for r in self:
        if r.state == "done":
            raise UserError(_("..."))
```

## Recordset operations

```python
records.filtered("active")
records.filtered(lambda r: r.hours > 8)
records.filtered_domain([("hours", ">", 8)])
records.mapped("name")
records.mapped("partner_id")
records.sorted(key="date", reverse=True)
records.ensure_one()
r1 | r2     # union
r1 & r2     # intersection
r1 - r2     # difference
records.exists()    # filter out deleted
```

## Environment

```python
self.env.user / self.env.company / self.env.context / self.env.cr
records.with_context(active_test=False)
records.with_user(user)
records.with_company(company)
records.sudo()              # bypass ACL/rules — DOCUMENT WHY
records.flush_recordset()
self.env.ref("module.xml_id")
```

## Field write commands (for One2many / Many2many)

```python
fields.Command.create({"name": "X"})        # create new related
fields.Command.update(id, {"name": "Y"})    # update existing
fields.Command.delete(id)                   # delete
fields.Command.unlink(id)                   # remove from set, don't delete
fields.Command.link(id)                     # add to set
fields.Command.clear()                      # remove all
fields.Command.set([1, 2, 3])               # replace
```

Tuple-based legacy syntax:
- `(0, 0, vals)` = create
- `(1, id, vals)` = update
- `(2, id)` = delete
- `(3, id)` = unlink
- `(4, id)` = link
- `(5,)` = clear
- `(6, 0, ids)` = set

Either works; `Command` is more readable.

## Search / read patterns

```python
records = self.env["res.partner"].search([("active", "=", True)], limit=10, order="name")
n = self.env["res.partner"].search_count([("active", "=", True)])
data = self.env["res.partner"].search_read(domain, ["name", "email"], limit=10)
groups = self.env["res.partner"]._read_group(
    domain, groupby=["country_id"], aggregates=["__count", "credit_limit:sum"]
)
record = self.env["res.partner"].browse(42)         # no SQL until accessed
records = self.env["res.partner"].browse([1, 2, 3]) # batched
```

## Common imports

```python
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare, float_round, format_date
```
