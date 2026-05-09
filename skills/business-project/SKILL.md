---
name: business-project
description: Odoo 17 Project (project) + Timesheets (hr_timesheet) + sale_timesheet + Tasks. Use when configuring project management, customizing task workflows, billing time to customers, building gantt schedules, or integrating with external PM tools.
---

# Business: Project Management (Odoo 17 — `project`)

## What this app solves

Plan and execute work:
- **Projects** — containers for tasks
- **Tasks** — units of work, kanban-able, assignable, time-trackable
- **Stages** — task lifecycle per project (or shared)
- **Subtasks** — task hierarchy
- **Timesheets** — hours logged against tasks (links to billing)
- **Milestones** — checkpoints
- **Gantt / planning** views (Enterprise)

Connects with Sale (billable services), HR (employee timesheets), Helpdesk (tickets to tasks), CRM (lead → task).

## Core models

| Model | Purpose |
|---|---|
| `project.project` | Project header |
| `project.task` | Task / activity |
| `project.task.type` | Stage |
| `project.tags` | Tags |
| `project.milestone` | Milestone within project |
| `account.analytic.line` (with `task_id`) | Timesheet entry |

## Task lifecycle

Stages are configurable per project (or shared with `project_ids = NULL`). Common pattern: To Do → In Progress → Review → Done. Closed/canceled = `is_closed=True` or via `state` if customized.

## Configuration

### Project setup
- Customer (links to billing)
- Privacy: Public / Followers / Customer / Internal
- Allow timesheets, allow milestones, allow recurring
- Default analytic account (for cost tracking)

### Stages
- Per project or shared
- Sequence
- Folded (collapsed in kanban by default)
- `is_closed` — terminal stage flag
- Optional: rating request on close

### Timesheet billing (sale_timesheet)
For service products with `service_policy = "delivered_timesheet"`:
- Sale order with service line confirms → creates project + task
- Hours logged on the task = "delivered quantity" on the SO line
- Invoicing the SO bills those hours

This is **the** Odoo professional services flow.

## Common customizations

### Custom task workflow with state machine
Beyond stages: real states with transitions.

```python
class ProjectTask(models.Model):
    _inherit = "project.task"

    state = fields.Selection([
        ("draft", "Draft"),
        ("ready", "Ready"),
        ("in_progress", "In progress"),
        ("blocked", "Blocked"),
        ("review", "Review"),
        ("done", "Done"),
    ], default="draft", tracking=True)

    blocked_reason = fields.Text()

    def action_block(self):
        for task in self:
            if not task.blocked_reason:
                raise UserError(_("Please specify a blocked reason."))
            task.state = "blocked"
            task.message_post(body=_("Blocked: %s") % task.blocked_reason)
```

### SLA / deadline tracking
```python
class ProjectTask(models.Model):
    _inherit = "project.task"
    sla_deadline = fields.Datetime(compute="_compute_sla", store=True)
    sla_status = fields.Selection([
        ("on_track", "On track"),
        ("at_risk", "At risk"),
        ("breached", "Breached"),
    ], compute="_compute_sla_status", store=True)

    @api.depends("create_date", "task_type_id")
    def _compute_sla(self):
        for task in self:
            if task.create_date and task.task_type_id.sla_hours:
                task.sla_deadline = task.create_date + timedelta(hours=task.task_type_id.sla_hours)
```

### Auto-assign to least-loaded team member
```python
@api.model_create_multi
def create(self, vals_list):
    for vals in vals_list:
        if not vals.get("user_ids") and vals.get("project_id"):
            project = self.env["project.project"].browse(vals["project_id"])
            user = self._pick_least_loaded(project.member_ids)
            if user:
                vals["user_ids"] = [(6, 0, [user.id])]
    return super().create(vals_list)

def _pick_least_loaded(self, candidates):
    counts = self.env["project.task"].read_group(
        [("user_ids", "in", candidates.ids), ("state", "not in", ("done", "cancel"))],
        ["user_ids"], ["user_ids"],
    )
    counts_by_user = {c["user_ids"][0]: c["user_ids_count"] for c in counts}
    return min(candidates, key=lambda u: counts_by_user.get(u.id, 0))
```

### Recurring tasks
Standard supports recurring tasks. Configure on the task: enable recurrence, set interval, end condition. Cron generates next occurrences.

### Milestones with auto-close
"When all tasks done, close milestone."

```python
class ProjectMilestone(models.Model):
    _inherit = "project.milestone"

    def _check_completion(self):
        for milestone in self:
            tasks = milestone.task_ids
            if tasks and all(t.is_closed for t in tasks):
                milestone.is_reached = True
```

Trigger from `project.task.write` when stage changes.

### Customer collaboration on tasks (Portal)
Standard: portal users can see assigned project tasks, comment, mark done. To restrict (only some types):

```python
class ProjectProject(models.Model):
    _inherit = "project.project"
    allow_portal_collaboration = fields.Boolean()
```

Then update access rules accordingly.

## Reports & dashboards

Standard:
- Project overview (kanban, list, gantt-Enterprise, calendar)
- Burndown (Enterprise)
- Workload analysis (Enterprise)
- Timesheet analysis

Common customs:
- "Project profitability" — billed hours × rate vs. cost (employee × hours)
- "Sprint velocity" — tasks closed per period

## Integration touchpoints

| Pattern | Approach |
|---|---|
| **CRM → Project** | When opportunity won, create project (custom on `crm.lead.action_set_won`) |
| **Sale → Project** | Service products with `service_tracking="task_in_project"` create projects |
| **Helpdesk → Project** | `helpdesk_mgmt_project` (OCA) or convert ticket to task |
| **External PM (Jira, Asana)** | Webhook receives task events; bi-directional sync via mapping table |
| **Email → Task** | Project alias creates tasks from email |
| **Slack notifications** | Mail messages → Slack via webhook |

## Common pitfalls

- Project privacy "Public" by default — customers see internal tasks. Set "Internal" or "Followers" by default.
- Custom state field that doesn't update `kanban_state` → kanban view colors don't reflect state.
- Timesheet without analytic account → can't roll up to project costing.
- `sale_timesheet` configured but customer's SO has wrong product type → timesheet doesn't auto-link.
- Recurring task generation cron not running → recurrences silently absent.
- Subtask hours rolled up to parent without filtering → double-counted in reports.

## OCA modules worth knowing

- `project_task_default_stage` — default stage per project
- `project_timeline` — gantt-style timeline (community)
- `project_task_dependency` — formal task dependencies
- `project_task_kpi` — KPI fields on tasks
- `project_role` — task roles instead of just users
- `project_template` — project templates with task lists

## References

- [Odoo Project documentation](https://www.odoo.com/documentation/17.0/applications/services/project.html)
- [Odoo Timesheets documentation](https://www.odoo.com/documentation/17.0/applications/services/timesheets.html)
- [OCA project](https://github.com/OCA/project)
