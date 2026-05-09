# Odoo Senior Engineer Pack

A comprehensive Claude Code / Cowork plugin pack that turns Claude into a senior Odoo engineer. Includes a specialized agent, skills, and slash commands for building production-grade Odoo modules following both **Odoo official guidelines** and **OCA (Odoo Community Association) standards**.

## Versioning strategy

This repo uses **one branch per Odoo version**. Each branch contains a complete, self-contained pack tuned for that specific Odoo version's APIs, conventions, and breaking changes.

| Branch | Odoo version | Status |
|--------|--------------|--------|
| [`17.0`](../../tree/17.0) | Odoo 17 | ✅ Complete |
| `18.0` | Odoo 18 | 🚧 Planned |
| `16.0` | Odoo 16 | 🚧 Planned |

`main` (this branch) only contains this index, contributing guide, and license. **All actual content lives in version branches.**

## What's in each version branch

```
.
├── .plugin.json                 # Plugin manifest (installable in Cowork / Claude Code)
├── agents/
│   └── odoo-{version}-senior-engineer.md
├── skills/                      # Domain-specific skills
│   ├── module-scaffolding/
│   ├── orm-models/
│   ├── views-and-actions/
│   ├── security-and-access/
│   ├── owl-frontend/
│   ├── qweb-reports/
│   ├── mixins-and-mail/
│   ├── wizards-and-actions/
│   ├── web-services-api/
│   ├── testing/
│   ├── performance/
│   ├── migration-{prev}-to-{this}/
│   ├── deployment/
│   └── oca-compliance/
├── commands/                    # Slash commands
│   ├── odoo-new-module.md
│   ├── odoo-review.md
│   ├── odoo-migrate.md
│   ├── odoo-add-field.md
│   ├── odoo-add-view.md
│   ├── odoo-add-report.md
│   ├── odoo-explain.md
│   └── odoo-debug.md
├── references/                  # Distilled cheat-sheets from official docs
└── examples/                    # Reference modules (minimal + advanced)
```

## Installation

Pick the branch that matches your Odoo version:

```bash
git clone -b 17.0 https://github.com/jmsuarez2005/odoo-senior-engineer-pack.git
```

Then install as a Claude Code / Cowork plugin (see the version branch's README for exact commands).

## Philosophy

A senior Odoo engineer:

1. **Knows the framework cold** — ORM internals, OWL, security model, QWeb
2. **Follows conventions** — both Odoo's official coding guidelines and OCA standards
3. **Thinks in modules** — clean separation, minimal coupling, proper dependencies
4. **Cares about performance** — avoids N+1, uses prefetch, indexes appropriately
5. **Tests everything** — unit, integration, tours
6. **Documents for the next person** — README, manifest, docstrings

This pack encodes those habits.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). To add support for a new Odoo version, branch from the closest existing version and update.

## License

[MIT](./LICENSE)
