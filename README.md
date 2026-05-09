# Odoo Senior Engineer — Odoo 17 (Claude Code Plugin)

A **Claude Code plugin** that turns Claude into a senior Odoo 17 engineer with both deep technical knowledge AND business-domain expertise. Built around the official Odoo 17 documentation and OCA standards.

> 🌳 This is the `17.0` branch. Each major Odoo version has its own branch — see [the index on `main`](../../tree/main) for the version map.

## Install

```bash
# In Claude Code:
/plugin install jmsuarez2005/odoo-senior-engineer-pack@17.0
```

Or from a local clone:
```bash
git clone -b 17.0 https://github.com/jmsuarez2005/odoo-senior-engineer-pack.git
# then in Claude Code:
/plugin install ./odoo-senior-engineer-pack
/reload-plugins
```

## What's inside

### 1 main agent

**`odoo-17-senior-engineer`** — the persona Claude adopts. Knows the framework cold, configures before customizing, and follows Odoo + OCA conventions.

### 20 skills

**Technical foundation (14)**
| Skill | Covers |
|---|---|
| `module-scaffolding` | Manifest, file layout, OCA-compliant README, dependencies |
| `orm-models` | Models, fields, decorators, recordsets, inheritance |
| `views-and-actions` | form / list (v17) / kanban / search / graph / pivot, actions, menus |
| `security-and-access` | ACLs, record rules, groups, sudo() vs with_user() |
| `mixins-and-mail` | mail.thread, activity, portal, image, utm, rating |
| `wizards-and-actions` | TransientModel, multi-step, mass-action |
| `qweb-reports` | QWeb syntax, paperformat, PDF reports |
| `owl-frontend` | OWL 2 components, services, hooks, registries, custom widgets |
| `web-services-api` | XML-RPC, JSON-RPC, controllers, REST, webhooks |
| `testing` | TransactionCase, HttpCase, browser tours, mocking |
| `performance` | N+1 avoidance, prefetch, indexes, profiling |
| `i18n-translations` | _() vs _lt(), .pot/.po, locale-aware formatting |
| `cron-and-queue` | ir.cron + OCA queue_job, retries, channels |
| `website-and-portal` | Public pages, snippets, customer portal |
| `debugging-deep` | Profiler, EXPLAIN ANALYZE, py-spy, log scoping |
| `migration-16-to-17` | Breaking changes, deprecations, upgrade scripts |
| `deployment` | Odoo.sh, self-hosted (nginx, workers), Docker, multi-DB |
| `oca-compliance` | pre-commit, pylint-odoo, README fragments, manifest |
| `ci-cd` | GitHub Actions / GitLab CI, multi-version matrix |
| `business-modeling` | Map real businesses to Odoo: config-vs-customize buckets |

**Business domain knowledge (12)**
| Skill | Apps covered | What you can do with it |
|---|---|---|
| `business-sales` | `sale_management` | Quote-to-cash, pricelists, commissions, custom approvals |
| `business-crm` | `crm` | Pipeline config, lead routing, scoring, automation |
| `business-accounting` | `account` / `account_accountant` | CoA, journals, taxes, fiscal positions, reconciliation |
| `business-inventory` | `stock` | Warehouses, routes, lots/serials, valuation |
| `business-mrp` | `mrp` | BOMs, work centers, subcontracting, kits |
| `business-purchase` | `purchase` | RFQs, POs, three-way match, blanket orders |
| `business-hr-payroll` | `hr`, `hr_payroll`, `hr_holidays`, `hr_timesheet`, `hr_expense`, `hr_recruitment` | Employee lifecycle, payroll, expenses, recruitment |
| `business-project` | `project`, `hr_timesheet`, `sale_timesheet` | Task workflows, billing time, milestones |
| `business-helpdesk` | `helpdesk` (Enterprise), OCA `helpdesk_mgmt` | Tickets, teams, SLAs, escalation |
| `business-ecommerce` | `website_sale` | Catalog, checkout, B2B vs B2C, multi-website |
| `business-subscriptions` | `sale_subscription` (Enterprise), OCA `subscription_oca` | Recurring revenue, MRR, dunning, proration |
| `business-pos` | `point_of_sale` | POS UI customization, kitchen printing, offline |
| `business-marketing` | `mass_mailing`, `marketing_automation`, `event`, `survey` | Campaigns, drip flows, attribution |

Each business skill covers: **what it solves**, the **core models**, the **lifecycle**, **configuration**, **common customizations** with code, **common pitfalls**, and **OCA modules worth knowing**.

### 13 slash commands

**Module / code level**
- `/odoo-new-module <name>` — scaffold an OCA-compliant module
- `/odoo-add-field <model> <field>` — add a field with all the boilerplate
- `/odoo-add-view <model> <type>` — generate a view
- `/odoo-add-report <model>` — scaffold a QWeb report
- `/odoo-review` — senior code review against Odoo + OCA checklists
- `/odoo-migrate-16-to-17` — analyze a v16 module, produce migration plan
- `/odoo-explain <symbol>` — deep explanation of an Odoo concept
- `/odoo-debug` — debugging triage
- `/odoo-profile` — performance profiling walkthrough

**Business / project level**
- `/odoo-business-fit <use_case>` — map a use case to Odoo, produce scoping doc
- `/odoo-customize-flow <flow> <change>` — plan a safe customization
- `/odoo-localize <country>` — country setup checklist
- `/odoo-data-import` — migration from legacy system

### References & examples

- `references/` — distilled cheat-sheets (ORM, OWL, migration deltas)
- `examples/` — `minimal_module` + `advanced_module` (full reference module with ACLs, record rules, chatter, wizard, OWL widget, REST, QWeb report)

## How to use

Once installed:

1. **Talk in business terms.** "We sell construction materials and need commission tracking per project" → Claude maps to `sale_management` + custom commission, asks the right questions, produces a scoping doc.

2. **Or in technical terms.** "Add an SLA field on `helpdesk.ticket` that's computed from priority and stage" → Claude writes the field, the compute, the view changes, the test.

3. **Use slash commands** for repeatable tasks: `/odoo-new-module hr_overtime`, `/odoo-business-fit "we run a dive school"`, `/odoo-review`.

4. **Trust the agent's judgment.** It will configure before customizing, push back on anti-patterns, and tell you when something is Enterprise-only.

## Philosophy

A senior Odoo engineer:
1. **Understands the business first**, not the tech
2. **Configures before customizing**, customizes before forking
3. **Knows the framework cold** — ORM, OWL, security, QWeb
4. **Cares about performance from day one** — no N+1, prefetch, indexes
5. **Tests everything** — unit, integration, tours
6. **Documents for the next person** — README, manifest, docstrings

This pack encodes those habits.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) on `main`. To add support for Odoo 18, branch from `17.0` to `18.0` and update.

## License

[MIT](./LICENSE) — see root.

## Sources

This pack distills:
- [Odoo 17 Developer Documentation](https://www.odoo.com/documentation/17.0/developer.html)
- [Odoo 17 Reference](https://www.odoo.com/documentation/17.0/developer/reference.html)
- [Odoo Coding Guidelines](https://www.odoo.com/documentation/17.0/contributing/development/coding_guidelines.html)
- [OCA Contributing Guide](https://github.com/OCA/odoo-community.org/blob/master/website/Contribution/CONTRIBUTING.rst)
- [pylint-odoo](https://github.com/OCA/pylint-odoo)
- [OCA addons across all repositories](https://github.com/OCA)
- [Claude Code plugins documentation](https://code.claude.com/docs/en/plugins)
