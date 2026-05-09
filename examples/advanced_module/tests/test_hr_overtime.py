# Copyright 2026 Jean Suarez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestHrOvertime(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env["hr.employee"].create({"name": "Test Employee"})
        cls.user_user = cls.env["res.users"].create({
            "name": "OT User",
            "login": "ot_user",
            "groups_id": [(6, 0, [cls.env.ref("advanced_module.group_overtime_user").id])],
        })
        cls.user_manager = cls.env["res.users"].create({
            "name": "OT Manager",
            "login": "ot_manager",
            "groups_id": [(6, 0, [cls.env.ref("advanced_module.group_overtime_manager").id])],
        })

    def _make_overtime(self, **kwargs):
        vals = {
            "employee_id": self.employee.id,
            "date": "2026-05-01",
            "hours": 4.0,
        }
        vals.update(kwargs)
        return self.env["hr.overtime"].create(vals)

    def test_creation_assigns_sequence_name(self):
        ot = self._make_overtime()
        self.assertNotEqual(ot.name, "New")
        self.assertTrue(ot.name.startswith("OT/"))

    def test_default_state_is_draft(self):
        ot = self._make_overtime()
        self.assertEqual(ot.state, "draft")

    def test_negative_hours_rejected(self):
        with self.assertRaises(Exception):  # SQL CHECK or ValidationError
            self._make_overtime(hours=-1.0)

    def test_excessive_hours_rejected(self):
        with self.assertRaises(ValidationError):
            self._make_overtime(hours=15.0)

    def test_user_cannot_approve(self):
        ot = self._make_overtime(state="submitted")
        with self.assertRaises(AccessError):
            ot.with_user(self.user_user).action_approve()

    def test_manager_can_approve(self):
        ot = self._make_overtime(state="submitted")
        ot.with_user(self.user_manager).action_approve()
        self.assertEqual(ot.state, "approved")

    def test_cannot_approve_draft(self):
        ot = self._make_overtime()
        with self.assertRaises(UserError):
            ot.with_user(self.user_manager).action_approve()

    def test_employee_overtime_count(self):
        self._make_overtime(state="approved")
        self._make_overtime(date="2026-05-02", hours=2.0, state="approved")
        self._make_overtime(date="2026-05-03", hours=1.0, state="draft")
        self.assertEqual(self.employee.overtime_count, 2)
        self.assertEqual(self.employee.overtime_hours_total, 6.0)
