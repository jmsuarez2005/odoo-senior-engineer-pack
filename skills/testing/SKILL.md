---
name: testing
description: Write Odoo 17 tests — TransactionCase, HttpCase, browser tours, --test-tags, mocking. Use when adding tests, debugging test failures, or planning a test strategy for a module.
---

# Testing (Odoo 17)

## When to use this skill

Any time you write or fix tests in an Odoo module, configure CI, or debug a flaky test.

## The three test classes

| Class | When | Speed |
|---|---|---|
| `TransactionCase` | ORM/business logic tests | Fast |
| `HttpCase` | End-to-end with browser tours | Slow |
| `BaseCase` | Pure unit tests (no DB) | Fastest |

`TransactionCase` rolls back its transaction at the end of each test, so tests are isolated and quick. Use it for 80%+ of your tests.

## TransactionCase example

```python
# tests/test_overtime.py
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError, AccessError


@tagged("post_install", "-at_install")
class TestOvertime(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env["hr.employee"].create({
            "name": "Test Employee",
        })
        cls.user_overtime = cls.env["res.users"].create({
            "name": "OT User",
            "login": "ot_user",
            "groups_id": [(6, 0, [cls.env.ref("hr_overtime.group_overtime_user").id])],
        })

    def test_create_default_state_is_draft(self):
        ot = self.env["hr.overtime"].create({
            "employee_id": self.employee.id,
            "date": "2026-05-01",
            "hours": 4.0,
        })
        self.assertEqual(ot.state, "draft")
        self.assertEqual(ot.name, ot.env["ir.sequence"].next_by_code("hr.overtime") or "New")

    def test_negative_hours_rejected(self):
        with self.assertRaises(ValidationError):
            self.env["hr.overtime"].create({
                "employee_id": self.employee.id,
                "date": "2026-05-01",
                "hours": -1.0,
            })

    def test_user_cannot_approve(self):
        ot = self.env["hr.overtime"].create({
            "employee_id": self.employee.id,
            "date": "2026-05-01",
            "hours": 4.0,
            "state": "submitted",
        })
        with self.assertRaises(AccessError):
            ot.with_user(self.user_overtime).action_approve()

    def test_approval_posts_message(self):
        ot = self.env["hr.overtime"].create({
            "employee_id": self.employee.id,
            "date": "2026-05-01",
            "hours": 4.0,
            "state": "submitted",
        })
        before = len(ot.message_ids)
        ot.action_approve()
        self.assertEqual(ot.state, "approved")
        self.assertGreater(len(ot.message_ids), before)
```

### Tagging

`@tagged("post_install", "-at_install")` is the standard for module tests:
- `at_install` — run during install (before other modules' post-install).
- `post_install` — run after all modules installed (where most module tests belong).
- `-at_install` — explicitly opt out of at-install run.

Custom tags let you filter at the CLI: `--test-tags=hr_overtime,my_special_tag`.

## Form helper — testing through a view

`Form` simulates filling a form view, including running onchanges and computes:

```python
from odoo.tests.common import Form

def test_overtime_form_workflow(self):
    with Form(self.env["hr.overtime"]) as form:
        form.employee_id = self.employee
        form.date = "2026-05-01"
        form.hours = 4.0
    overtime = form.record  # already saved
    self.assertEqual(overtime.state, "draft")
```

## HttpCase + browser tours

For UI flows (form interactions, button clicks, wizard sequences):

```python
# tests/test_overtime_tours.py
from odoo.tests.common import HttpCase, tagged


@tagged("-at_install", "post_install")
class TestOvertimeTours(HttpCase):

    def test_submit_overtime_tour(self):
        self.start_tour("/web", "hr_overtime.tour_submit_overtime", login="admin")
```

The tour itself in JS:

```js
/** @odoo-module **/

import { registry } from "@web/core/registry";
import { stepUtils } from "@web_tour/tour_service/tour_utils";

registry.category("web_tour.tours").add("hr_overtime.tour_submit_overtime", {
    test: true,
    url: "/odoo/overtime",
    steps: () => [
        {
            content: "Click New",
            trigger: ".o_list_button_add",
            run: "click",
        },
        {
            content: "Fill employee",
            trigger: "div[name='employee_id'] input",
            run: "edit Test Employee",
        },
        {
            content: "Pick autocomplete option",
            trigger: ".dropdown-item:contains('Test Employee')",
            run: "click",
        },
        {
            content: "Fill hours",
            trigger: "input[name='hours']",
            run: "edit 4.0",
        },
        ...stepUtils.saveForm(),
        {
            content: "Submit",
            trigger: "button[name='action_submit']",
            run: "click",
        },
        {
            content: "Verify state",
            trigger: ".o_statusbar_status [data-value='submitted'].o_arrow_button_current",
        },
    ],
});
```

Add the tour file to `web.assets_tests` in the manifest:
```python
"assets": {
    "web.assets_tests": [
        "hr_overtime/static/tests/tours/*.js",
    ],
},
```

## Running tests

```bash
# All tests in the module
odoo -d test_db -i hr_overtime --test-enable --stop-after-init

# Only a specific tag
odoo -d test_db -i hr_overtime --test-enable --test-tags=hr_overtime --stop-after-init

# Only a specific class or method
odoo -d test_db -i hr_overtime --test-enable --test-tags=/hr_overtime:TestOvertime.test_negative_hours_rejected --stop-after-init
```

`-i` installs the module first time. Use `-u` to upgrade if already installed.

## Mocking

Avoid mocking when possible — Odoo's transaction-rollback model makes most things testable for real. When you must mock (external HTTP calls, time, randomness):

```python
from unittest.mock import patch

def test_external_call_handled(self):
    with patch("odoo.addons.hr_overtime.models.hr_overtime.requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"ref": "PR-001"}
        self.overtime.action_send_to_payroll()
        self.assertEqual(self.overtime.payroll_ref, "PR-001")
        mock_post.assert_called_once()
```

For time, use `freezegun`:
```python
from freezegun import freeze_time

@freeze_time("2026-05-01 12:00:00")
def test_today_default(self):
    ot = self.env["hr.overtime"].create({"employee_id": self.employee.id, "hours": 1})
    self.assertEqual(str(ot.date), "2026-05-01")
```

## Useful test utilities

```python
self.assertRecordValues(record, [{"name": "x", "state": "draft"}])  # batch field check
self.cr.flush()                                                     # force pending writes
self.env.invalidate_all()                                           # drop all caches
with self.mute_logger("odoo.sql_db"):                               # silence expected errors
    ...
```

## Test data — fixtures

Define common setup in `tests/common.py`:

```python
from odoo.tests.common import TransactionCase

class HrOvertimeCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env["hr.employee"].create({"name": "Common Employee"})
        # ... shared fixtures
```

Then inherit:
```python
from .common import HrOvertimeCommon

class TestApprove(HrOvertimeCommon):
    def test_approve(self):
        # cls.employee available
        ...
```

## Common pitfalls

- Tests that rely on shared mutable state from another test → flake. Each test should set up what it needs.
- Forgetting `@tagged("post_install", "-at_install")` → tests run at install time when dependent modules aren't ready.
- Using `time.sleep` in tours → unreliable. Use `trigger:` + appropriate selector, OWL waits for it.
- Hardcoded record IDs (`self.env.ref("base.partner_demo")` is fine; `self.env["res.partner"].browse(42)` is not).
- Asserting on `record.message_ids` length without flushing → message_post may queue.
- Mocking what you should set up for real → makes refactors painful. Prefer real records over mocks.
- Tests that depend on `--demo` data → demo isn't always loaded. Create your own fixtures.
- Running with `--test-enable` but no `--test-tags=` and a huge DB → runs every test in every installed module.

## CI checklist

- [ ] Tests pass with `--test-enable --stop-after-init`
- [ ] No `print()` or `breakpoint()` left in
- [ ] Test names describe the behavior, not the method (`test_negative_hours_rejected`, not `test_create_2`)
- [ ] Each test has at least one `assert*`
- [ ] No tests skipped without a comment explaining why
- [ ] `tests/__init__.py` imports every test module

## References

- [Odoo 17 — Testing](https://www.odoo.com/documentation/17.0/developer/reference/backend/testing.html)
- [Odoo 17 — Tours](https://www.odoo.com/documentation/17.0/developer/howtos/website_themes/website_themes_tour.html)
