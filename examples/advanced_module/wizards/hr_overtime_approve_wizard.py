# Copyright 2026 Jean Suarez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class HrOvertimeApproveWizard(models.TransientModel):
    _name = "hr.overtime.approve.wizard"
    _description = "Approve Overtime Wizard"

    overtime_id = fields.Many2one("hr.overtime", required=True, readonly=True)
    note = fields.Text(string="Note")
    notify = fields.Boolean(string="Notify employee", default=True)

    def action_confirm(self):
        self.ensure_one()
        self.overtime_id.action_approve()
        if self.note:
            self.overtime_id.message_post(body=_("Approval note: %s") % self.note)
        return {"type": "ir.actions.act_window_close"}
