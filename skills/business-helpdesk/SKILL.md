---
name: business-helpdesk
description: Odoo 17 Helpdesk (helpdesk, Enterprise) + community alternatives (helpdesk_mgmt OCA) — tickets, teams, SLA, KB, customer portal. Use when setting up support, customizing escalation rules, integrating chat/email channels, or building knowledge bases.
---

# Business: Helpdesk (Odoo 17)

## What this app solves

Customer support ticketing:
- **Tickets** — customer issue records
- **Teams** — support groups with stages, SLAs, channels
- **SLA Policies** — response/resolution time targets
- **Knowledge Base** — articles for self-service
- **Channels** — email alias, web form, live chat, API
- **Customer rating** — post-resolution feedback

`helpdesk` is **Enterprise-only** in standard Odoo. The community alternative is OCA's `helpdesk_mgmt`.

## Core models (Enterprise `helpdesk`)

| Model | Purpose |
|---|---|
| `helpdesk.ticket` | The ticket |
| `helpdesk.team` | Support team |
| `helpdesk.stage` | Stage (per team) |
| `helpdesk.sla` | SLA policy |
| `helpdesk.sla.status` | SLA status on a ticket |
| `helpdesk.ticket.type` | Ticket category |

## Configuration

### Teams
- Members
- Channels (email alias, website form, live chat tag)
- Default assignment (manual / round-robin / random)
- Stages (per team)
- Self-service config (portal, KB)
- Performance — SLA enabled, rating, etc.

### SLAs
- Target time (response or close)
- Conditions (priority, category, customer)
- Calendar-aware (business hours)

### Stages
- Sequence, fold (closed)
- Email template for stage transitions (e.g. auto-reply when entering "In Progress")
- "is closed" flag for terminal stages

## Customizations

### Auto-routing tickets to teams
```python
class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("team_id"):
                vals["team_id"] = self._auto_route(vals).id
        return super().create(vals_list)

    def _auto_route(self, vals):
        Team = self.env["helpdesk.team"]
        if vals.get("priority") == "3":  # high
            return Team.search([("name", "=", "Tier 2")], limit=1)
        if "vip" in (vals.get("tag_ids") or []):
            return Team.search([("name", "=", "VIP Support")], limit=1)
        return Team.search([("name", "=", "General")], limit=1)
```

### Custom escalation
"If unanswered after 4 hours, escalate to manager":

```python
@api.model
def _cron_escalate(self):
    cutoff = fields.Datetime.now() - timedelta(hours=4)
    stale = self.search([
        ("stage_id.is_close", "=", False),
        ("create_date", "<", cutoff),
        ("user_id", "!=", False),
    ])
    for t in stale:
        if t.team_id.user_id and not t.escalated:
            t.user_id = t.team_id.user_id  # reassign to team manager
            t.escalated = True
            t.message_post(body=_("Escalated to manager."))
```

### Conversion to task / sale order
Common: helpdesk → project task for follow-up dev work, or → sale order for billable consulting.

```python
def action_convert_to_task(self):
    self.ensure_one()
    return {
        "type": "ir.actions.act_window",
        "res_model": "project.task",
        "view_mode": "form",
        "target": "current",
        "context": {
            "default_name": self.name,
            "default_partner_id": self.partner_id.id,
            "default_description": self.description,
        },
    }
```

### Customer portal customization
Standard portal `/my/tickets` works. To allow customers to upload attachments, reply, see knowledge base — extend `controllers/portal.py`.

### Custom rating logic
Standard: `rating.mixin`. Default: 3 emoji feedback, optional comment. To send rating request via email after close:

```python
def write(self, vals):
    res = super().write(vals)
    if "stage_id" in vals:
        for t in self.filtered("stage_id.is_close"):
            t.rating_send_request()
    return res
```

## OCA `helpdesk_mgmt` (community alternative)

If you can't use Enterprise:
- `helpdesk_mgmt` — base ticketing
- `helpdesk_mgmt_project` — convert tickets to project tasks
- `helpdesk_mgmt_sale` — convert to sale orders
- `helpdesk_mgmt_timesheet` — log time on tickets

Lighter than Enterprise but covers core use cases.

## Reports

Standard:
- Tickets by stage / team
- SLA compliance
- Performance — agent leaderboard
- Customer satisfaction (rating)

## Integration touchpoints

| Pattern | Approach |
|---|---|
| **Email → Ticket** | Team alias auto-creates tickets |
| **Webform → Ticket** | `website_helpdesk_form` ships a snippet |
| **Live chat → Ticket** | `helpdesk_livechat` integration |
| **External monitoring (Datadog, PagerDuty) → Ticket** | Webhook → ticket creation with tags/priority |
| **Slack notification on new ticket** | Mail message → Slack webhook |
| **Phone call (Aircall, Twilio)** | OCA `crm_phonecall` or custom controller |

## Common pitfalls

- Creating ticket types that overlap with tags → users confused which to use.
- SLA enabled but business calendar not set → SLA always considers 24/7, breaches faster than expected.
- Email alias on team that gets spam → flooded with junk tickets. Use spam filtering at MTA level.
- Customer portal exposing ticket fields with sensitive internal info — review template carefully.
- Custom stage with `is_close=True` but missing rating trigger → no satisfaction data.
- Auto-rating sent before agent has had time to act → bad rating habit.

## References

- [Odoo Helpdesk documentation](https://www.odoo.com/documentation/17.0/applications/services/helpdesk.html)
- [OCA helpdesk](https://github.com/OCA/helpdesk)
