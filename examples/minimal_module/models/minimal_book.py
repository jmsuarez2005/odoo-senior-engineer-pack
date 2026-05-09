# Copyright 2026 Jean Suarez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class MinimalBook(models.Model):
    _name = "minimal.book"
    _description = "Minimal Book"
    _order = "title"

    title = fields.Char(required=True, index=True)
    author = fields.Char()
    pages = fields.Integer()
    tag = fields.Selection(
        [("fiction", "Fiction"), ("non_fiction", "Non-fiction")],
        default="fiction",
    )
    is_thick = fields.Boolean(compute="_compute_is_thick", store=True)

    @api.depends("pages")
    def _compute_is_thick(self):
        for record in self:
            record.is_thick = record.pages > 400
