---
name: business-crm
description: Odoo 17 CRM (crm) — leads, opportunities, pipeline, activities, lead scoring, lost reasons, conversion to sale. Use when configuring or customizing the CRM pipeline, multi-team setups, automated lead assignment, lead enrichment, or integration with marketing automation and external lead sources.
---

# Business: CRM (Odoo 17 — `crm`)

## What this app solves

Manages the journey from "we got a lead" to "we won a deal":

- **Lead** — early-stage interest (often unqualified)
- **Opportunity** — qualified lead with a stage, salesperson, expected revenue
- **Pipeline** — kanban of opportunities by stage
- **Sales Team** — group of salespeople with shared pipeline rules
- **Activity** — scheduled actions (call, meeting, email)
- **Lost reason** — taxonomy of "why we lost"

It feeds into Sales (quotation from opportunity), Marketing (lead capture from campaigns), and Reporting (conversion rates, win/loss analysis).

## Core models

| Model | Purpose |
|---|---|
| `crm.lead` | Lead AND opportunity (`type` field distinguishes) |
| `crm.team` | Sales team |
| `crm.stage` | Pipeline stage (per team or shared) |
| `crm.lost.reason` | Reason taxonomy |
| `crm.tag` | Free-form tags |
| `utm.campaign` / `utm.source` / `utm.medium` | Marketing attribution |
| `crm.activity.report` | Reporting on activities (SQL view) |

`crm.lead` has `type = "lead"` or `type = "opportunity"`. Many companies skip the lead stage and go straight to opportunities — set "Leads" off in CRM settings to simplify.

## Lifecycle (opportunities)

`new` → `qualified` → `proposition` → `won` / `lost`

Stages are per team (or shared with `team_id = NULL`). Each stage has `is_won = True` for terminal won states.

`probability` is computed by a Bayesian model on stage + lead fields (the "Predictive Lead Scoring" feature). You can override it manually.

## Configuration — what the consultant sets up

### Sales teams
- Create a team per business unit / geography / product line
- Assign team leader + members
- Configure team-level dashboards, alias email, lead targets

### Pipeline stages
- Stages can be shared (team_id NULL) or team-specific
- Set `sequence` for ordering
- Set `is_won = True` on the final winning stage
- Optional: probability per stage (overrides predictive)

### Lead capture sources
- **Web form** (built-in CRM website module): direct form → `crm.lead`
- **Email alias**: each team has a `crm.team.alias` (e.g. `sales@example.com`); incoming mail creates lead/opportunity automatically
- **API** (`/web/dataset/call_kw` or REST): for external integrations
- **Manual entry**: salespeople create from "+ New" in pipeline

### Lead assignment
- Manual, or via "Lead Generation" automation rules (Enterprise: Auto-assign with scoring)
- Round-robin via `crm.team.assign_lead` cron
- Geographic / segment-based via custom domain on the team

### Lost reasons
Always populate this list. "Lost — competitor X", "Lost — budget", "Lost — wrong fit". Lost analysis is one of the most valuable CRM reports; it depends on this taxonomy.

## Common customizations

### Custom stage transitions
Stages are records, not code. Adding a new stage = creating a `crm.stage` record. Renaming = editing.

But if you want **transition rules** ("can't go from Qualified to Won without a quote"), you'll write Python:

```python
class CrmLead(models.Model):
    _inherit = "crm.lead"

    def write(self, vals):
        if "stage_id" in vals:
            new_stage = self.env["crm.stage"].browse(vals["stage_id"])
            if new_stage.is_won:
                for lead in self:
                    if not lead.order_ids.filtered(lambda o: o.state in ("sale", "done")):
                        raise UserError(_("Cannot win without a confirmed sale order."))
        return super().write(vals)
```

### Lead scoring beyond standard
Standard: predictive lead scoring on `probability`. To add custom scoring:

```python
class CrmLead(models.Model):
    _inherit = "crm.lead"
    custom_score = fields.Integer(compute="_compute_custom_score", store=True, index=True)

    @api.depends("country_id", "industry_id", "expected_revenue", "tag_ids")
    def _compute_custom_score(self):
        for lead in self:
            score = 0
            if lead.country_id.code in ("US", "GB", "DE", "FR"): score += 20
            if lead.industry_id.name in ("Technology", "Finance"): score += 15
            if lead.expected_revenue > 50000: score += 30
            if any(tag.name == "warm" for tag in lead.tag_ids): score += 10
            lead.custom_score = score
```

Then sort the pipeline by `custom_score` and use it in assignment rules.

### Opportunity routing on creation
A common ask: "leads from the contact form go to team A; leads from the partner webhook go to team B; high-value leads always go to the strategic team."

```python
class CrmLead(models.Model):
    _inherit = "crm.lead"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("team_id"):
                vals["team_id"] = self._auto_route_team(vals).id
        return super().create(vals_list)

    @api.model
    def _auto_route_team(self, vals):
        Team = self.env["crm.team"]
        if vals.get("expected_revenue", 0) > 100000:
            return Team.search([("name", "=", "Strategic")], limit=1)
        if vals.get("source_id") == self.env.ref("utm.utm_source_partner").id:
            return Team.search([("name", "=", "Channel")], limit=1)
        return Team.search([], order="member_count desc", limit=1)
```

### Activity SLAs
"If no contact in 3 days, escalate." Use `mail.activity` + a cron:

```python
@api.model
def _cron_escalate_stale(self):
    cutoff = fields.Datetime.now() - timedelta(days=3)
    stale = self.search([
        ("type", "=", "opportunity"),
        ("stage_id.is_won", "=", False),
        ("activity_ids.date_deadline", "<", cutoff),
    ])
    for lead in stale:
        lead.message_post(body=_("Escalating: no activity in 3+ days"))
        lead.user_id = lead.team_id.user_id
```

### Lead enrichment
Standard: Odoo's "Lead Enrichment" (Enterprise) calls Clearbit-like API on creation. To roll your own:

```python
@api.model_create_multi
def create(self, vals_list):
    leads = super().create(vals_list)
    for lead in leads:
        if lead.email_from and not lead.partner_name:
            lead.with_delay()._enrich_from_email()  # use queue_job
    return leads
```

## Reports & dashboards

Standard:
- **Pipeline analysis** — by stage, salesperson, expected revenue
- **Activities** — scheduled vs done, by user
- **Win/loss analysis** — by lost reason, source, salesperson

Customizing: most teams want a "monthly conversion funnel" with custom segmentation. Build on `crm.lead` with `read_group` and a custom view, or extend `crm.opportunity.report` (SQL view).

## Integration touchpoints

| Direction | Pattern |
|---|---|
| **Web form → CRM** | `website_crm` ships a form snippet → creates `crm.lead` |
| **Email → CRM** | Team's mail alias auto-creates leads from incoming mail |
| **CRM → Sale** | `crm.lead.action_new_quotation()` creates draft sale order linked back |
| **CRM → Project** | When you win, sometimes auto-create a project (custom) |
| **External CRM sync (HubSpot, Salesforce)** | Webhook receiver + custom controller; `external_id` field for idempotency |
| **Marketing automation** | `marketing_automation` triggers on `crm.lead` events; CRM enriches lead from campaign attribution |

## Common pitfalls

- Two people working the same lead simultaneously — Odoo doesn't lock leads. Use record rules + activity ownership conventions.
- Lead duplicate detection: standard checks email + partner. Configure threshold in CRM > Configuration. For more, use OCA `partner_duplicate_mgmt`.
- Stage soup: 15 stages because every salesperson wanted theirs. Keep ≤ 7 — pipeline gets unreadable.
- `probability = 100` on a non-won stage — confuses reporting. Use `is_won` flag instead.
- Closing a lead by archiving instead of marking lost — kills your "lost reasons" data.
- Bidirectional sync with external CRM without proper idempotency — duplicate lead pile.

## OCA modules worth knowing

- `crm_lead_lost_reason_required` — force selecting a lost reason
- `crm_phonecall` — restored phonecall model (removed from standard)
- `crm_lead_owner` — separate "owner" from "salesperson"
- `crm_lead_to_task` — convert lead to project task
- `partner_duplicate_mgmt` — duplicate detection across partners

## References

- [Odoo CRM documentation](https://www.odoo.com/documentation/17.0/applications/sales/crm.html)
- [OCA crm](https://github.com/OCA/crm)
