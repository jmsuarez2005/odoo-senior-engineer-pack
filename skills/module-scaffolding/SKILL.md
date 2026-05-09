---
name: module-scaffolding
description: Create a new Odoo 17 module with the correct file layout, manifest, and OCA-compliant README. Triggered by "new module", "create a module", "scaffold", "__manifest__.py", or whenever a fresh Odoo addon needs to be started.
---

# Module Scaffolding (Odoo 17)

## When to use this skill

You are creating a brand-new Odoo 17 addon, or auditing an existing one against the standard layout. This skill covers file structure, the manifest, dependencies, and the OCA README format.

## The canonical file layout

```
my_module/
├── __init__.py                # imports models, controllers, wizards, ...
├── __manifest__.py            # module metadata
├── README.rst                 # OCA-format README (or .md if not targeting OCA)
├── data/                      # XML data records loaded with noupdate=1 by default
│   └── ir_sequence_data.xml
├── demo/                      # demo data (only loaded with --demo)
│   └── demo.xml
├── i18n/                      # translations
│   └── es.po
├── models/
│   ├── __init__.py
│   └── res_partner.py         # one file per model, snake_case after the model
├── controllers/
│   ├── __init__.py
│   └── main.py
├── wizards/
│   ├── __init__.py
│   └── partner_merge_wizard.py
├── reports/
│   ├── __init__.py
│   ├── partner_report.py      # if there's logic
│   ├── partner_report.xml     # paperformat + report action
│   └── partner_report_template.xml  # QWeb template
├── views/
│   ├── res_partner_views.xml  # one file per model, suffixed _views
│   ├── menu_views.xml
│   └── assets.xml             # asset bundle declarations
├── security/
│   ├── ir.model.access.csv
│   ├── security_groups.xml
│   └── record_rules.xml
├── static/
│   ├── description/
│   │   ├── icon.png           # 140×140 PNG, required for app store
│   │   └── index.html         # marketing page
│   └── src/
│       ├── js/
│       ├── scss/
│       └── xml/               # OWL templates
├── tests/
│   ├── __init__.py
│   ├── common.py              # shared test setup
│   └── test_partner.py
└── doc/                       # OCA fragment system (optional)
    ├── changelog.rst
    ├── description.rst
    ├── configure.rst
    ├── usage.rst
    └── credits.rst
```

## The manifest

The `__manifest__.py` is a Python dict literal. **Do not** put logic in it — it's evaluated at registry build time.

```python
# -*- coding: utf-8 -*-
{
    "name": "HR Overtime",
    "version": "17.0.1.0.0",                    # see versioning rule below
    "summary": "Track and approve employee overtime hours",
    "description": """
HR Overtime
===========
Lets HR managers approve overtime requests submitted by employees.
""",
    "author": "Jean Suarez, Odoo Community Association (OCA)",
    "website": "https://github.com/jmsuarez2005/odoo-senior-engineer-pack",
    "license": "AGPL-3",                        # or "LGPL-3", "OEEL-1" for enterprise
    "category": "Human Resources",
    "depends": [
        "hr",
        "mail",
    ],
    "data": [
        # security FIRST — it's loaded before any model uses it in views
        "security/security_groups.xml",
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        # data
        "data/ir_sequence_data.xml",
        # views (in dependency order)
        "views/hr_overtime_views.xml",
        "views/menu_views.xml",
        # reports
        "reports/overtime_report.xml",
        "reports/overtime_report_template.xml",
    ],
    "demo": [
        "demo/demo.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "hr_overtime/static/src/js/**/*",
            "hr_overtime/static/src/scss/**/*",
            "hr_overtime/static/src/xml/**/*",
        ],
    },
    "installable": True,
    "application": False,                       # True only if it shows up as an "App"
    "auto_install": False,
    "external_dependencies": {
        "python": ["python-dateutil"],          # only if not already an Odoo dep
    },
}
```

### Versioning rule

`{odoo_version}.{module_major}.{module_minor}.{module_patch}` — for Odoo 17, that's `17.0.X.Y.Z`. Bump:
- patch (Z) for bugfixes
- minor (Y) for new features that don't require migration
- major (X) for breaking changes / required migrations

The leading `17.0` is **not** the module version — it's the Odoo series. Don't drop it.

### Data file ordering

The `data` list is loaded **in order**. Order matters:

1. `security/security_groups.xml` — groups must exist before anything references them
2. `security/ir.model.access.csv` — ACLs before views (views can reference groups)
3. `security/record_rules.xml`
4. `data/*.xml` — sequences, mail templates, cron jobs
5. `views/*.xml` — views in dependency order (parents before children)
6. `reports/*.xml`

If you get `ValueError: External ID not found in the system: ...`, you have a load order problem.

## The `__init__.py` files

Top-level:

```python
from . import models
from . import controllers
from . import wizards
from . import reports
```

In `models/__init__.py`:

```python
from . import hr_overtime
from . import hr_employee  # if you extend an existing model
```

**Order matters here too** — if `hr_employee.py` references `hr_overtime`, import `hr_overtime` first. Most of the time, alphabetical works.

## OCA-compliant README (using fragments)

OCA modules don't write `README.rst` by hand. They write fragments in `doc/` and let `oca-gen-addon-readme` assemble the final `README.rst`:

- `doc/description.rst` — what does this module do, in 2-3 sentences
- `doc/configure.rst` — what the user needs to configure after install
- `doc/usage.rst` — how to use the features
- `doc/changelog.rst` — version history
- `doc/credits.rst` — authors, contributors, financial backers

If you're not targeting OCA, a hand-written `README.md` is fine, but include those same five sections.

## Naming conventions

- **Module technical name**: `snake_case`, lowercase, descriptive. `hr_overtime`, not `HrOvertime` or `hr-overtime`.
- **Model name** (`_name`): `snake_case` with dots for namespacing. `hr.overtime`, not `hr_overtime` (the model's `_name` uses dots; the table name uses underscores automatically).
- **Field names**: `snake_case`. Boolean fields named affirmatively (`active`, not `is_inactive`). Many2one fields end with `_id`, One2many/Many2many with `_ids`.
- **XML record IDs**: `<model>_<purpose>` lowercase. `view_hr_overtime_form`, `action_hr_overtime`, `menu_hr_overtime_root`.
- **External IDs across modules**: prefix with module name when referenced from other modules.

## Common pitfalls

- **Forgetting `installable: True`** — module silently doesn't appear in Apps.
- **Wrong `category`** — the App store filters by category; pick one that exists or matches an existing app's category.
- **Putting data files in `demo`** — demo is only loaded with `--demo`, so production won't have your data.
- **Loading views before security** — `groups=` references will fail with cryptic ID-not-found errors.
- **Using `application: True` for a sub-module** — only set it on the "head" module of a feature area.
- **Empty `__init__.py` in `models/`** — Python won't load the model classes, so they don't register. Symptom: model not in `ir.model`.

## References

- [Odoo 17 — Module manifests](https://www.odoo.com/documentation/17.0/developer/reference/backend/module.html)
- [Odoo 17 — Coding guidelines: structure](https://www.odoo.com/documentation/17.0/contributing/development/coding_guidelines.html)
- [OCA Contributing Guide](https://github.com/OCA/odoo-community.org/blob/master/website/Contribution/CONTRIBUTING.rst)
- [oca-gen-addon-readme](https://github.com/OCA/maintainer-tools)
