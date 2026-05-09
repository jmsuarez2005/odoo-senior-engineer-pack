# Advanced Example: Overtime Management

A reference Odoo 17 module that demonstrates the full stack:

- **Models**: `hr.overtime` (new) + `hr.employee` (extension)
- **Mixins**: `mail.thread` + `mail.activity.mixin` (chatter + activities)
- **Security**: groups, ACL CSV, record rules (per-user + multi-company)
- **Views**: form, list, search, with inherited employee stat button
- **Wizard**: TransientModel-backed approve dialog
- **Controller**: REST endpoint with bearer auth
- **Frontend**: OWL 2 custom field widget
- **Reports**: QWeb PDF with `web.external_layout`
- **Email**: mail template
- **Tests**: 8 tests covering ACL, state transitions, computes

## What to look at first

1. `__manifest__.py` — file ordering, asset bundle, depends
2. `security/security_groups.xml` + `record_rules.xml` — security model
3. `models/hr_overtime.py` — full v17 idiomatic model
4. `models/hr_employee.py` — `_read_group` pattern (no N+1)
5. `static/src/js/components/overtime_badge.js` — OWL 2 custom widget
6. `controllers/main.py` — REST endpoint with `auth="bearer"`
7. `tests/test_hr_overtime.py` — what good tests look like

## Install

```bash
odoo -d test_db -i advanced_module --test-enable --stop-after-init
```

## Note

This module shows patterns. It's not production-ready — for a real overtime feature, you'd integrate with payroll, add date-range constraints, define cron jobs for nudges, etc.
