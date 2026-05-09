---
name: business-modeling
description: Map a real-world business process to Odoo 17 — pick the right standard apps, decide config-vs-customize, design custom modules that fit the existing data model. Use when starting a new Odoo project, evaluating fit for a use case, scoping customizations, or deciding "Studio vs custom code vs change the process".
---

# Business Modeling for Odoo (Odoo 17)

## When to use this skill

A client says "we sell construction materials and need to track commissions per project". A product manager says "we want field technicians to log hours from their phone". A founder says "we need a CRM but custom for our hospitality flow". You need to map the business to Odoo before writing a single line of code.

## The three-question filter

Before designing any custom module, run every requirement through:

1. **Does standard Odoo already do this?** (Configuration only)
2. **Can Studio / view inheritance solve it?** (Low-code)
3. **Does it need a real custom module?** (Code)

The senior bias is **don't customize what Odoo already does**. You'll fight upgrades forever, and the standard module probably handles edge cases you haven't thought of.

## Discovery: what to ask the client

Before scoping, get answers to:

### Process
- What's the lifecycle of the thing they're tracking? (Stages, transitions, who triggers each)
- What's the SLA / required latency at each stage?
- Where do humans intervene vs systems?

### Data
- What entities exist? (Customer, Order, Product, Project, …)
- What's the cardinality? (1 customer to N orders, etc.)
- What's the volume? (10 orders/day or 10K?)

### Roles
- Who creates, approves, edits, deletes each kind of record?
- Multi-company? Multi-warehouse? Multi-team?
- Are there external roles (customers via portal, suppliers)?

### Reporting
- What KPIs matter?
- What reports do they print/email today?
- What dashboards do they wish they had?

### Integration
- What external systems exist? (Accounting, payment gateway, e-commerce, marketing)
- Direction (Odoo→external, external→Odoo, both)?
- Real-time or batch?

## The standard apps map

When a use case comes in, you ask "which standard apps cover this?". Here's the canonical mapping (refer to specific business skills for depth):

| Business process | Primary apps | Common companions |
|---|---|---|
| B2B sales pipeline | `crm` | `mail`, `calendar` |
| B2B order-to-cash | `sale_management`, `account` | `stock`, `delivery` |
| B2C webshop | `website_sale` (eCommerce) | `payment`, `delivery`, `account` |
| Inventory + warehousing | `stock` | `delivery`, `purchase`, `mrp` |
| Manufacturing | `mrp` | `stock`, `purchase`, `quality` |
| Procurement | `purchase` | `stock`, `account` |
| Accounting + invoicing | `account_accountant` (Enterprise) or `account` | `payment`, fiscal localizations |
| HR core | `hr` | `hr_holidays`, `hr_attendance`, `hr_recruitment` |
| Payroll | `hr_payroll` (Enterprise + localization) | `hr`, `account` |
| Employee expenses | `hr_expense` | `account` |
| Time tracking | `hr_timesheet` | `project`, `sale_timesheet` |
| Project management | `project` | `hr_timesheet`, `mail`, `sale_timesheet` |
| Helpdesk / tickets | `helpdesk` (Enterprise) | `mail`, `sale_subscription` |
| Subscriptions / SaaS billing | `sale_subscription` (Enterprise) | `account`, `payment` |
| Field service | `industry_fsm` (Enterprise) | `project`, `stock`, `sale` |
| POS / retail | `point_of_sale` | `stock`, `account` |
| Marketing automation | `mass_mailing`, `marketing_automation` | `crm`, `event` |
| Events | `event`, `event_sale` | `website` |
| Surveys | `survey` | `crm`, `hr_recruitment` |
| Documents | `documents` (Enterprise) | `mail` |
| Approvals | `approvals` | — |
| Knowledge base | `knowledge` (Enterprise) | — |
| Quality control | `quality` | `mrp`, `stock` |
| Asset / equipment | `maintenance` | `hr` |

## Deciding fit: the four buckets

For each requirement, classify into one of:

### Bucket 1 — Standard, just configure
The feature exists. The work is configuration:
- Adjust company / chart of accounts
- Set up product variants, pricelists, tax groups
- Configure cron jobs (reminders, stat refreshes)
- Set up automated email templates
- Define groups and add users to them

**Time estimate**: hours to days. **Maintenance cost**: near zero.

### Bucket 2 — Studio / view inheritance (low-code)
Standard model is right, but the form needs an extra field, or a list needs a different filter, or a pipeline stage needs adding.

- Studio (Enterprise): no-code field/view editor
- Custom module with `_inherit` extending the existing model and adding a few fields

**Time estimate**: days. **Maintenance cost**: low (small surface).

### Bucket 3 — Custom module, fits the existing model
A new feature, but it composes with existing models cleanly.
- Example: "Track overtime per employee" — new model `hr.overtime`, FK to `hr.employee`, inherits `mail.thread`, integrates via stat button on employee form. No standard model is the right home, but the new model fits the framework.

**Time estimate**: weeks. **Maintenance cost**: medium.

### Bucket 4 — Custom module, fundamentally new domain
A whole subsystem Odoo doesn't have. Real estate property management, livestock breeding, diving school certifications.
- New models, possibly new app menu, full custom UX.

**Time estimate**: months. **Maintenance cost**: high.

## Anti-patterns

### "Recreate Excel in Odoo"
The client has a spreadsheet that does what they want. They ask you to build "the same thing" in Odoo. **Don't.** Map the spreadsheet to existing apps; nine times out of ten Excel was a workaround for Odoo not being there.

### "Replace standard module entirely"
The client's accounting team has opinions. They want a "simpler accounting module" that doesn't fully respect double-entry. Refuse politely. Standard `account` exists because accounting has rules. Customize within it (custom report, custom analytic flow, custom journal); don't rewrite it.

### "Each customer gets their own model"
Tempted to create `crm_lead_acme`, `crm_lead_globex` for two customers because their fields differ. Use one model with optional fields, conditional view rendering, and filtered ACL/rules.

### "Configure the standard, then override 80% of it"
Sometimes you start configuring `sale.order` and end up with 30 inherited overrides. This is a sign the customer's process **diverges from Odoo's model**. Two options:
1. Adapt their process to Odoo's (the upgrade-friendly path)
2. Build a parallel custom flow that doesn't try to fit `sale.order` (the customization-heavy path)

Pick one consciously, not by accident.

### "Build for the demo, not for production"
Demo data is small, perfect, single-language, single-currency. Production isn't. Always design with:
- Empty states (what does it look like with no data?)
- Bulk operations (how does mass approval work?)
- Multi-company, multi-currency, multi-language from day 1
- Performance at 100K records (not 100)

## A proper scoping document

For any new project, write down:

```markdown
## Use Case: <name>

### Business goal
What business outcome does this enable? (revenue, efficiency, compliance)

### Process
1. <step 1: who does what>
2. <step 2>
...

### Data model
- New entities: <list with fields>
- Extended entities: <list with which fields added>
- Reused entities: <list>

### Standard Odoo coverage
| Requirement | Standard? | App | Configuration / Customization |
|---|---|---|---|

### Customizations
| Item | Bucket (1/2/3/4) | Effort | Notes |
|---|---|---|---|

### Integrations
| System | Direction | Volume | Latency requirement |
|---|---|---|---|

### Roles & ACL
| Role | Can | Cannot |
|---|---|---|

### Reports & dashboards
- <list>

### KPIs
- <list>

### Migrations from current system
- <data sources, transformation needs, cutover plan>

### Risks
- <list>

### Out of scope
- <explicit list to manage expectations>
```

This document is the contract between you and the client. Refer to it when scope creeps.

## When to push back

A senior says no when:

- The client wants to disable double-entry accounting "to keep things simple"
- "We need it next week" but the scope is 3 months of work
- The customization conflicts with a standard upgrade path
- The integration requires synchronous calls to a flaky external API in the user request cycle
- They want to remove an audit trail "because users complain about chatter"
- They want unique IDs that depend on a sequence the user can edit

In each case: explain why, offer the alternative that meets the underlying need, document the decision.

## Senior's working method on a new project

1. **Understand the business first**, not the tech. Sit with users, watch them work for a day if possible.
2. **Inventory standard Odoo coverage** — what apps map to what they do today.
3. **Write the scoping doc** — bucket every requirement.
4. **Prototype on a clean Odoo install** — config-only first. Show the client.
5. **Iterate on customizations** — smallest reasonable bucket per requirement.
6. **Plan the data migration** before writing any custom code. (If you can't get data in, customizations don't matter.)
7. **Test with realistic volume** — not 5 records, not 5 million. The actual size.
8. **Document for the next person.** README, manifests, comments. Always.

## References

- [Odoo Apps overview](https://www.odoo.com/page/all-apps)
- See domain skills: `business-sales`, `business-crm`, `business-accounting`, `business-inventory`, `business-mrp`, `business-purchase`, `business-hr-payroll`, `business-project`, `business-helpdesk`, `business-ecommerce`, `business-subscriptions`, `business-pos`, `business-marketing`
