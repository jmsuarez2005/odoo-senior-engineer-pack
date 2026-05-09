# Copyright 2026 Jean Suarez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
from odoo import http
from odoo.http import request, Response


class HrOvertimeController(http.Controller):

    @http.route("/api/v1/overtime", type="http", auth="bearer", methods=["GET"])
    def list_overtime(self, **kwargs):
        """List overtime visible to the authenticated user (respecting ACL)."""
        domain = []
        state = kwargs.get("state")
        if state:
            domain.append(("state", "=", state))
        records = request.env["hr.overtime"].search_read(
            domain,
            ["id", "name", "employee_id", "date", "hours", "state"],
            limit=100, order="date desc",
        )
        return Response(json.dumps(records, default=str), content_type="application/json")

    @http.route("/api/v1/overtime", type="json", auth="bearer", methods=["POST"])
    def submit_overtime(self, employee_id, hours, date, justification=None):
        """Submit a new overtime request."""
        overtime = request.env["hr.overtime"].create({
            "employee_id": employee_id,
            "hours": hours,
            "date": date,
            "justification": justification,
            "state": "submitted",
        })
        return {"id": overtime.id, "name": overtime.name, "state": overtime.state}
