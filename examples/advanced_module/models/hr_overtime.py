# Copyright 2026 Jean Suarez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class HrOvertime(models.Model):
    _name = "hr.overtime"
    _description = "Employee Overtime"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"
    _check_company_auto = True

    name = fields.Char(
        required=True, copy=False, default="New", tracking=True, readonly=True
    )
    employee_id = fields.Many2one(
        "hr.employee", required=True, tracking=True, index=True, check_company=True,
    )
    date = fields.Date(default=fields.Date.context_today, required=True, tracking=True)
    hours = fields.Float(digits=(4, 2), required=True, tracking=True)
    justification = fields.Text()
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("approved", "Approved"),
            ("refused", "Refused"),
        ],
        default="draft",
        required=True,
        copy=False,
        tracking=True,
        index=True,
    )
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company, index=True,
    )

    _sql_constraints = [
        ("hours_positive", "CHECK(hours > 0)", "Overtime hours must be positive."),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("hr.overtime") or "New"
                )
        return super().create(vals_list)

    @api.constrains("hours")
    def _check_hours_max(self):
        for record in self:
            if record.hours > 12:
                raise ValidationError(
                    _("Overtime cannot exceed 12 hours in a single day.")
                )

    def action_submit(self):
        for record in self:
            if record.state != "draft":
                raise UserError(_("Only draft overtime can be submitted."))
            record.state = "submitted"
            record.message_post(body=_("Submitted for approval."))

    def action_approve(self):
        if not self.env.user.has_group(
            "advanced_module.group_overtime_manager"
        ):
            raise AccessError(_("Only managers can approve overtime."))
        for record in self:
            if record.state != "submitted":
                raise UserError(_("Only submitted overtime can be approved."))
            record.state = "approved"
            record._send_approval_email()

    def action_refuse(self):
        if not self.env.user.has_group(
            "advanced_module.group_overtime_manager"
        ):
            raise AccessError(_("Only managers can refuse overtime."))
        for record in self:
            if record.state != "submitted":
                raise UserError(_("Only submitted overtime can be refused."))
            record.state = "refused"

    def action_open_approve_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Approve Overtime"),
            "res_model": "hr.overtime.approve.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_overtime_id": self.id},
        }

    def _send_approval_email(self):
        self.ensure_one()
        template = self.env.ref(
            "advanced_module.email_template_overtime_approved", raise_if_not_found=False
        )
        if template:
            template.send_mail(self.id, force_send=False)
