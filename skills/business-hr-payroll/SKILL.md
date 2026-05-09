---
name: business-hr-payroll
description: Odoo 17 HR (hr) + Payroll (hr_payroll) + Time Off + Attendance + Expenses + Recruitment + Appraisal — employee lifecycle, contracts, payslips, leaves, time tracking. Use when configuring HR processes, building custom payroll rules per locale, employee self-service, or HR analytics.
---

# Business: HR & Payroll (Odoo 17)

## What this app suite solves

End-to-end employee lifecycle:
- **`hr`** — employees, departments, jobs, contracts, organization
- **`hr_recruitment`** — jobs, applicants, hiring pipeline
- **`hr_holidays`** — time off / leave management
- **`hr_attendance`** — clock-in / clock-out
- **`hr_timesheet`** — log hours per project/task
- **`hr_expense`** — employee expense reports
- **`hr_payroll`** (Enterprise) — payslip generation with country localizations
- **`hr_appraisal`** (Enterprise) — performance reviews

## Core models

| Model | Purpose |
|---|---|
| `hr.employee` | The employee record |
| `hr.department` | Org structure |
| `hr.job` | Job position |
| `hr.contract` | Employment contract (start/end, salary, schedule) |
| `hr.applicant` | Job applicant |
| `hr.leave` | Time off request |
| `hr.leave.type` | Leave category (paid, sick, unpaid, …) |
| `hr.leave.allocation` | Leave balance allocation per employee per type |
| `hr.attendance` | Clock-in/out record |
| `account.analytic.line` (with `project_id`) | Timesheet entry |
| `hr.expense` | Expense line |
| `hr.expense.sheet` | Expense report (group of lines) |
| `hr.payslip` | Payslip |
| `hr.payslip.line` | Salary rule output (basic, OT, deductions) |
| `hr.salary.rule` | A computation rule |
| `hr.contract.history` | Contract changes over time |

## Configuration — what the consultant sets up

### Employees
- Personal info, work info (manager, department, job)
- Private info (address, family — separate ACL group)
- Resource calendar (working hours)
- Timezone

### Contracts
- One employee can have multiple contracts over time (only one `running` at a time)
- Salary structure (drives which payroll rules apply)
- Resource calendar (overrides employee's)
- Wage, period, working schedule

### Working schedules (`resource.calendar`)
- Daily attendance lines (Mon 9–13, 14–17, etc.)
- Global leaves (public holidays)
- Per-employee or per-contract calendar

### Leaves
- **Leave types**: per company, per country localization
- Allocation rules: monthly accrual, fixed allocation, carry-over
- Approval levels: manager only, HR only, both

### Payroll structures (Enterprise)
- A **structure** (e.g. "Spanish payroll") groups **rules**
- Each rule is a Python expression on contract + worked days
- Rules feed into payslip lines (basic, social security, IRPF, net)

Country localizations (`l10n_es_hr_payroll`, `l10n_fr_hr_payroll`, etc.) ship the legal rules. **Use them.** Don't hand-roll payroll for countries with localizations — the legal complexity is staggering.

## Common customizations

### Custom leave type with custom approval
```python
class HrLeave(models.Model):
    _inherit = "hr.leave"

    def _validate_leave_request(self):
        for leave in self:
            if leave.holiday_status_id.code == "SABBATICAL":
                if not leave.employee_id.years_of_service >= 5:
                    raise UserError(_("Sabbatical requires 5+ years of service."))
        return super()._validate_leave_request()
```

### Custom timesheet validation
"Timesheet hours must match attendance hours per day":

```python
class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    @api.constrains("date", "employee_id", "unit_amount")
    def _check_attendance_match(self):
        for line in self:
            if not line.employee_id or line.unit_amount <= 0: continue
            day_lines = self.search([
                ("date", "=", line.date),
                ("employee_id", "=", line.employee_id.id),
            ])
            total_ts = sum(day_lines.mapped("unit_amount"))
            day_attendance = self.env["hr.attendance"].search([
                ("employee_id", "=", line.employee_id.id),
                ("check_in", ">=", line.date),
                ("check_in", "<", line.date + timedelta(days=1)),
            ])
            attendance_hours = sum(a.worked_hours for a in day_attendance)
            if attendance_hours and total_ts > attendance_hours:
                raise ValidationError(_(
                    "Timesheet (%.2f) exceeds attendance (%.2f) on %s",
                    total_ts, attendance_hours, line.date,
                ))
```

### Custom salary rule
For a specific localization or company addition (e.g., "remote work allowance"):

```python
# In data
<record id="rule_remote_allowance" model="hr.salary.rule">
    <field name="name">Remote Work Allowance</field>
    <field name="code">REMOTE</field>
    <field name="category_id" ref="hr_payroll.ALW"/>
    <field name="condition_select">python</field>
    <field name="condition_python">contract.work_location_type == 'home'</field>
    <field name="amount_select">fix</field>
    <field name="amount_fix">100.0</field>
    <field name="struct_id" ref="hr_payroll.structure_base"/>
</record>
```

### Approval workflow on expenses
Standard: 1-step manager approval. To insert finance:

```python
class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    state = fields.Selection(selection_add=[
        ("finance_review", "Finance review"),
    ], ondelete={"finance_review": "set draft"})

    def approve_expense_sheets(self):
        for sheet in self:
            if sheet.total_amount > 1000:
                sheet.state = "finance_review"
                continue
            super(HrExpenseSheet, sheet).approve_expense_sheets()
```

### Recruitment → Employee onboarding
Standard: `hr.applicant.create_employee_from_applicant()` creates the employee. To extend with onboarding tasks:

```python
class HrApplicant(models.Model):
    _inherit = "hr.applicant"

    def create_employee_from_applicant(self):
        action = super().create_employee_from_applicant()
        employee = self.env["hr.employee"].browse(action["res_id"])
        # Auto-assign onboarding project tasks
        onboarding_template = self.env.ref("my_module.onboarding_project_template")
        onboarding_template.copy({"name": f"Onboarding: {employee.name}"})
        return action
```

### Time off accruals beyond standard
Standard supports calendar-based accruals (X days per month). For service-year-based ("after 5 years, +2 days/year"), build a cron that adjusts allocations.

## Reports

Standard:
- Payslip PDF
- Time off report
- Attendance overview
- Expense reports

Custom common: "Headcount by department by month", "Overtime trends", "Time off usage by team", "Payroll cost analysis". Build on the right model with read_group.

## Integration touchpoints

| Pattern | Approach |
|---|---|
| **HRIS sync (Workday, BambooHR)** | Bi-directional via REST; `external_id` on employee for idempotency |
| **Biometric clock-in** | Webhook → creates `hr.attendance` |
| **Payroll → Bank** | After payslip done, generate SEPA file with `account_payment_order` |
| **Time off → Calendar** | Standard integrates with `calendar` |
| **Expense receipt OCR** | Use OCR service (Veryfi, Mindee) → fills `hr.expense` fields |
| **LinkedIn / Indeed → Recruitment** | Email parsing into `hr.applicant` (alias) or API |

## Privacy & compliance

HR data is heavily regulated (GDPR, HIPAA-like, country-specific labor laws):
- ACL: standard `hr.group_hr_user` and `hr.group_hr_manager` separate views
- Private info section on employee form has its own group (`hr.group_hr_user`)
- For very sensitive (medical, ID), use OCA `hr_employee_private_info` or build group-gated fields
- Audit trail via chatter on every HR record

Payroll is even more sensitive:
- `hr_payroll` has its own access groups
- Payslips visible to the employee (their own only) via portal
- Locked once posted

## Common pitfalls

- Storing salary in a `Float` instead of `Monetary` → multi-currency breaks.
- Computing leave balance from `hr.leave` only — ignore allocations, get wrong number. Use `hr.leave.allocation` aggregations.
- Writing custom payslip rules without testing every legally-required scenario (overtime, sick leave, partial month). Use the localization's structure as the base.
- Modifying past payslips after posting → corrupts payroll history. Use rollback/recompute via standard tools.
- Direct write to `hr.attendance.check_out` without `worked_hours` recompute → reports off.
- Multi-company employees: an employee can be linked to multiple companies (`company_ids`), but contracts are per-company. Confusion arises from this nuance.

## OCA modules worth knowing

- `hr_employee_calendar_planning` — variable working time
- `hr_attendance_overtime` — overtime auto-calc from attendance
- `hr_holidays_compute_days` — better leave duration computation
- `hr_expense_advance_clearing` — employee advances and clearing
- `hr_recruitment_skill` — skills and matching
- `payroll_*` (multiple) — extra payroll features
- `hr_employee_id` — government IDs with country validation

## References

- [Odoo HR documentation](https://www.odoo.com/documentation/17.0/applications/hr.html)
- [Odoo Payroll (Enterprise)](https://www.odoo.com/documentation/17.0/applications/hr/payroll.html)
- [OCA hr](https://github.com/OCA/hr)
- [OCA payroll](https://github.com/OCA/payroll)
