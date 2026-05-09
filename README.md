# Odoo Senior Engineer Pack

A **Claude Code plugin** that turns Claude into a senior Odoo engineer with deep **technical** AND **business-domain** knowledge. Covers everything from ORM internals to mapping real businesses to standard Odoo apps.

## Versioning strategy

This repo uses **one branch per Odoo version**. Each branch contains a complete, self-contained plugin tuned for that version's APIs, conventions, and breaking changes.

| Branch | Odoo version | Status | Skills | Commands |
|--------|--------------|--------|--------|----------|
| [`17.0`](../../tree/17.0) | Odoo 17 | ✅ Complete (20 skills, 13 commands) | 20 | 13 |
| `18.0` | Odoo 18 | 🚧 Planned | — | — |
| `16.0` | Odoo 16 | 🚧 Planned | — | — |

`main` (this branch) only contains this index, contributing guide, and license. **All actual content lives in version branches.**

## Install

Pick the branch that matches your Odoo version, in Claude Code:

```bash
/plugin install jmsuarez2005/odoo-senior-engineer-pack@17.0
```

Then check `[the version branch's README](../../tree/17.0)` for the full feature list and usage.

## What's in each version branch

```
.
├── .claude-plugin/
│   └── plugin.json                  # Claude Code plugin manifest
├── agents/
│   └── odoo-{version}-senior-engineer.md
├── skills/                          # Technical + business skills
│   ├── module-scaffolding/
│   ├── orm-models/
│   ├── ...
│   ├── business-sales/
│   ├── business-crm/
│   ├── business-accounting/
│   └── ...
├── commands/                        # Slash commands
│   ├── odoo-new-module.md
│   ├── odoo-business-fit.md
│   ├── odoo-customize-flow.md
│   └── ...
├── references/                      # Distilled cheat-sheets
└── examples/                        # Reference modules
```

## What this plugin makes Claude great at

### As a developer
- Building OCA-compliant modules with idiomatic v17 patterns
- ORM design (fields, computes, inheritance, recordsets)
- OWL 2 frontend (components, services, registries)
- Security (ACLs, record rules, multi-company)
- QWeb reports
- Performance (prefetch, indexes, profiling)
- Migration from v16

### As a business analyst / consultant
- Mapping real-world processes to standard Odoo apps
- Knowing what's standard, what's Enterprise, what's OCA
- Scoping projects with config-vs-customize discipline
- Localization (chart of accounts, taxes, payroll, e-invoicing)
- Data migration from legacy systems
- Identifying when to push back on bad customization ideas

### Across all Odoo apps
Sales, CRM, Accounting, Inventory, Manufacturing, Purchase, HR + Payroll + Time-off + Attendance + Timesheets + Expenses + Recruitment, Project, Helpdesk, eCommerce, Subscriptions, POS, Marketing.

## Philosophy

A senior Odoo engineer:
1. **Understands the business first**, not the tech
2. **Configures before customizing**, customizes before forking
3. **Knows the framework cold** — ORM, OWL, security, QWeb
4. **Cares about performance from day one**
5. **Tests everything**
6. **Documents for the next person**

This pack encodes those habits.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). To add support for a new Odoo version, branch from the closest existing version.

## License

[MIT](./LICENSE)
