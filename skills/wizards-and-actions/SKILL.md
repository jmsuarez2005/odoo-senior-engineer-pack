---
name: wizards-and-actions
description: Build Odoo 17 wizards (TransientModel) and the actions they return. Use when creating multi-step user flows, "Confirm" dialogs that need data entry, mass-action wizards, or any TransientModel-backed UI.
---

# Wizards & Actions (Odoo 17)

## When to use this skill

You need a transient form to collect input from the user and then act on the underlying records. Examples: "Approve overtime with reason", "Merge partners", "Send by email" dialog, "Mass-update price list".

## The mental model

A wizard is a `TransientModel` — a model whose records live for ~1 hour in the same DB tables, then get garbage-collected. The user fills the form, clicks a button, and the button method does the real work and returns an action describing what to show next.

## Minimal wizard

```python
# wizards/hr_overtime_approve_wizard.py
from odoo import models, fields, api, _


class HrOvertimeApproveWizard(models.TransientModel):
    _name = "hr.overtime.approve.wizard"
    _description = "Approve Overtime Wizard"

    overtime_id = fields.Many2one("hr.overtime", required=True, readonly=True)
    note = fields.Text(string="Note to employee")
    notify = fields.Boolean(string="Send email", default=True)

    @api.model
    def default_get(self, fields_list):
        # Pre-fill from active context (set by the calling action)
        defaults = super().default_get(fields_list)
        active_id = self.env.context.get("active_id")
        if active_id and self.env.context.get("active_model") == "hr.overtime":
            defaults["overtime_id"] = active_id
        return defaults

    def action_confirm(self):
        self.ensure_one()
        self.overtime_id.write({"state": "approved"})
        if self.note:
            self.overtime_id.message_post(body=self.note)
        if self.notify:
            template = self.env.ref("hr_overtime.email_template_overtime_approved")
            template.send_mail(self.overtime_id.id)
        return {"type": "ir.actions.act_window_close"}
```

## The wizard view

```xml
<record id="view_hr_overtime_approve_wizard_form" model="ir.ui.view">
    <field name="name">hr.overtime.approve.wizard.form</field>
    <field name="model">hr.overtime.approve.wizard</field>
    <field name="arch" type="xml">
        <form string="Approve Overtime">
            <group>
                <field name="overtime_id"/>
                <field name="note" placeholder="Optional note for the employee"/>
                <field name="notify"/>
            </group>
            <footer>
                <button name="action_confirm" string="Approve"
                        type="object" class="btn-primary"/>
                <button string="Cancel" class="btn-secondary" special="cancel"/>
            </footer>
        </form>
    </field>
</record>
```

`special="cancel"` is the Odoo idiom for the close-without-saving button.

## The action that opens the wizard

```xml
<record id="action_hr_overtime_approve_wizard" model="ir.actions.act_window">
    <field name="name">Approve Overtime</field>
    <field name="res_model">hr.overtime.approve.wizard</field>
    <field name="view_mode">form</field>
    <field name="target">new</field>     <!-- modal -->
    <field name="binding_model_id" ref="model_hr_overtime"/>
    <field name="binding_view_types">form,list</field>
</record>
```

`target="new"` makes it a modal. Setting `binding_model_id` adds it to the Action menu of `hr.overtime` automatically.

## Returning actions from buttons

A button method's return value tells the client what to do next. Common shapes:

### Open another form
```python
return {
    "type": "ir.actions.act_window",
    "name": _("Approved Overtime"),
    "res_model": "hr.overtime",
    "view_mode": "form",
    "res_id": self.overtime_id.id,
    "target": "current",
}
```

### Open a list filtered
```python
return {
    "type": "ir.actions.act_window",
    "name": _("Pending Overtimes"),
    "res_model": "hr.overtime",
    "view_mode": "list,form",
    "domain": [("state", "=", "submitted")],
    "context": {"search_default_my_overtime": 1},
}
```

### Open another wizard
```python
return {
    "type": "ir.actions.act_window",
    "res_model": "hr.overtime.notify.wizard",
    "view_mode": "form",
    "target": "new",
    "context": {"default_overtime_id": self.overtime_id.id},
}
```

### Close (after success)
```python
return {"type": "ir.actions.act_window_close"}
```

### Reload the underlying view
```python
return {"type": "ir.actions.client", "tag": "reload"}
```

### Display a notification
```python
return {
    "type": "ir.actions.client",
    "tag": "display_notification",
    "params": {
        "title": _("Approved"),
        "message": _("%s overtime requests approved.") % len(records),
        "type": "success",            # success | warning | danger | info
        "sticky": False,
        "next": {"type": "ir.actions.act_window_close"},
    },
}
```

### Open a URL (download or external)
```python
return {
    "type": "ir.actions.act_url",
    "url": "/web/binary/download/...",
    "target": "self",
}
```

### Run a report
```python
return self.env.ref("hr_overtime.report_overtime").report_action(self.overtime_id)
```

## Multi-step wizard

Use a state field + view inheritance, or a sequence of `act_window` returns.

### State field pattern (single view, conditional rendering)
```python
class MyWizard(models.TransientModel):
    _name = "my.wizard"

    state = fields.Selection([("step1", "Step 1"), ("step2", "Step 2"), ("done", "Done")],
                             default="step1")
    name = fields.Char()
    confirmed = fields.Boolean()

    def action_next(self):
        self.write({"state": "step2"})
        return {"type": "ir.actions.act_window", "res_model": self._name,
                "view_mode": "form", "res_id": self.id, "target": "new"}
```

Form view uses `invisible="state != 'step1'"` etc. Reasonable for 2-3 steps.

### Sequence pattern (one wizard per step)
For more complex flows, prefer one TransientModel per step with explicit transitions. Easier to test, easier to reason about.

## Mass-action wizards (active_ids)

When invoked from the Action menu of a list:

```python
@api.model
def default_get(self, fields_list):
    defaults = super().default_get(fields_list)
    active_ids = self.env.context.get("active_ids", [])
    active_model = self.env.context.get("active_model")
    if active_model == "hr.overtime" and active_ids:
        defaults["overtime_ids"] = [(6, 0, active_ids)]
    return defaults

overtime_ids = fields.Many2many("hr.overtime")
```

Use `(6, 0, ids)` to set a Many2many to a list of IDs. See [ORM commands](https://www.odoo.com/documentation/17.0/developer/reference/backend/orm.html#odoo.fields.Command).

## Garbage collection

Transient records older than `ir.config_parameter` `transient.gc.limit` (default 100 records per model, kept for ~1h) get auto-cleaned by a cron. This means:

- **Don't rely on a wizard record being there long-term.** Don't store anything important there.
- **Don't create huge intermediate datasets in TransientModel.** Use the persistent model + `active=False` if you need durability.

## Common pitfalls

- Forgetting `target="new"` on the action — opens as a full page instead of modal.
- Using `target="new"` on a wizard that returns another `target="new"` action — works, but each modal stacks. Set `next: {act_window_close}` to dismiss after notification.
- Returning `None` from a button when you wanted to close — Odoo treats it as "do nothing", so the dialog stays. Return `{"type": "ir.actions.act_window_close"}` explicitly.
- Reading from `self.env.context.get("active_ids")` and silently iterating an empty list — guard with an early return.
- Defining a wizard that mirrors an existing model — that's not a wizard, that's an unnecessary model. Wizards are for **transient** input.
- Mass-action wizard that writes one record at a time in a Python loop — use `recordset.write({...})` to batch.

## References

- [Odoo 17 — TransientModel](https://www.odoo.com/documentation/17.0/developer/reference/backend/orm.html#odoo.models.TransientModel)
- [Odoo 17 — Actions](https://www.odoo.com/documentation/17.0/developer/reference/backend/actions.html)
