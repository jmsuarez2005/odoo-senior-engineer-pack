# Copyright 2026 Jean Suarez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    overtime_ids = fields.One2many("hr.overtime", "employee_id", string="Overtimes")
    overtime_count = fields.Integer(
        compute="_compute_overtime_count", string="Overtime Count"
    )
    overtime_hours_total = fields.Float(
        compute="_compute_overtime_count", string="Total Overtime Hours"
    )

    def _compute_overtime_count(self):
        # Single read_group to avoid N+1
        groups = self.env["hr.overtime"]._read_group(
            domain=[("employee_id", "in", self.ids), ("state", "=", "approved")],
            groupby=["employee_id"],
            aggregates=["__count", "hours:sum"],
        )
        counts = {emp.id: (count, hours) for emp, count, hours in groups}
        for employee in self:
            count, hours = counts.get(employee.id, (0, 0.0))
            employee.overtime_count = count
            employee.overtime_hours_total = hours

    def action_view_overtimes(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Overtimes",
            "res_model": "hr.overtime",
            "view_mode": "list,form",
            "domain": [("employee_id", "=", self.id)],
            "context": {"default_employee_id": self.id},
        }
