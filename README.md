# Odoo Senior Engineer Pack — Odoo 17.0

A Claude Code / Cowork plugin that turns Claude into a senior Odoo 17 engineer. Built around the **official Odoo 17 documentation** and **OCA (Odoo Community Association) standards**.

> 🌳 This is the `17.0` branch. Each major Odoo version has its own branch — see [the index on `main`](../../tree/main) for the full version map.

## What's inside

### One main agent
- **`odoo-17-senior-engineer`** — the persona Claude adopts. Knows ORM, OWL 2, security, QWeb, mixins, testing, performance, and follows both Odoo and OCA conventions cold.

### 14 skills

| Skill | What it covers |
|---|---|
| `module-scaffolding` | Manifest, file layout, OCA-compliant README, dependencies |
| `orm-models` | Models, fields, decorators, recordsets, inheritance (`_inherit`, `_inherits`, delegation) |
| `views-and-actions` | form / list / kanban / search / graph / pivot / activity views, window/server actions, menus |
| `security-and-access` | `ir.model.access.csv`, record rules, groups, `sudo()` vs `with_user()` |
| `mixins-and-mail` | `mail.thread`, `mail.activity.mixin`, `portal.mixin`, `image.mixin`, chatter wiring |
| `wizards-and-actions` | `TransientModel`, multi-step wizards, return actions |
| `qweb-reports` | QWeb syntax, paperformat, PDF reports, headers/footers |
| `owl-frontend` | OWL 2 components, services, hooks, registries, custom field/view widgets |
| `web-services-api` | XML-RPC, JSON-RPC, controllers, REST patterns, authentication |
| `testing` | `TransactionCase`, `HttpCase`, tours, `--test-tags`, mocking |
| `performance` | N+1 avoidance, prefetch, indexes, `flush_model`, query profiling |
| `migration-16-to-17` | Breaking changes, deprecations, upgrade scripts |
| `deployment` | Odoo.sh, self-hosted (nginx, workers, longpolling), multi-DB |
| `oca-compliance` | pre-commit, pylint-odoo, manifest checklist, README fragments |

### 8 slash commands

| Command | What it does |
|---|---|
| `/odoo-new-module <name>` | Scaffold an OCA-compliant module |
| `/odoo-review` | Senior-grade code review against Odoo + OCA checklists |
| `/odoo-migrate-16-to-17` | Analyze a v16 module and produce a migration plan |
| `/odoo-add-field <model> <field>` | Add a field with all the boilerplate (XML, security, tests) |
| `/odoo-add-view <model> <type>` | Generate a view |
| `/odoo-add-report <model>` | Scaffold a QWeb report |
| `/odoo-explain <symbol>` | Deep explanation of an Odoo concept (decorator, mixin, hook…) |
| `/odoo-debug` | Debugging checklist (logs, `--dev=all`, test tags…) |

### References & examples

- `references/` — distilled cheat-sheets for ORM, OWL, QWeb, security, migration deltas
- `examples/` — minimal and advanced reference modules with full structure

## Installation

### As a Cowork / Claude Code plugin

```bash
git clone -b 17.0 https://github.com/jmsuarez2005/odoo-senior-engineer-pack.git
cd odoo-senior-engineer-pack
# Install via Cowork:
#   /plugin install ./
# Or copy to your plugins directory.
```

### Using individual pieces

You can also drop just the skills you want into your own project under `.claude/skills/`, or copy individual slash commands into `.claude/commands/`.

## Usage

Once installed, Claude will:

1. Adopt the senior engineer persona automatically when discussing Odoo 17 work
2. Trigger the right skill based on what you're doing (e.g., asking about `_inherit` triggers `orm-models`)
3. Respond to slash commands like `/odoo-new-module my_module`

Try:

```
/odoo-new-module hr_overtime
/odoo-review
/odoo-explain @api.depends
```

## Philosophy

A senior Odoo engineer doesn't just write code that works — they write code that another engineer can pick up two years from now. This pack encodes that bar:

- **Follow conventions, don't invent them.** Odoo and OCA have opinions. We follow them.
- **Security first.** Every model gets ACLs. Every public method gets a permission check.
- **Performance is a feature.** No N+1, prefetch the right fields, index foreign keys you query.
- **Test the contract.** `TransactionCase` for ORM, `HttpCase` + tours for UX flows.
- **Documentation is part of the deliverable.** README, manifest, docstrings, no exceptions.

## License

[MIT](./LICENSE) — see root.

## Sources

This pack distills the following authoritative resources:

- [Odoo 17 Developer Documentation](https://www.odoo.com/documentation/17.0/developer.html)
- [Odoo 17 Reference](https://www.odoo.com/documentation/17.0/developer/reference.html)
- [Odoo Coding Guidelines](https://www.odoo.com/documentation/17.0/contributing/development/coding_guidelines.html)
- [OCA Contributing Guide](https://github.com/OCA/odoo-community.org/blob/master/website/Contribution/CONTRIBUTING.rst)
- [pylint-odoo](https://github.com/OCA/pylint-odoo)
- [OCA maintainer-tools](https://github.com/OCA/maintainer-tools)
