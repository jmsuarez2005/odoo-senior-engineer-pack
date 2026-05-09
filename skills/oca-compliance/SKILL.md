---
name: oca-compliance
description: Make a module pass OCA standards — pre-commit, pylint-odoo, README fragments, manifest checklist, license headers. Use when preparing a module for OCA submission, setting up CI for an OCA-style repo, or auditing existing modules against OCA conventions.
---

# OCA Compliance (Odoo 17)

## When to use this skill

You're either contributing to OCA, building an in-house module that should follow OCA conventions, or setting up CI for an OCA-style repo.

## What "OCA compliance" actually means

A short list of conventions that make modules portable, reviewable, and consistent across thousands of OCA addons:

1. **License**: AGPL-3 (most common for OCA), LGPL-3, or specific exceptions.
2. **Manifest**: full metadata, declared author including "Odoo Community Association (OCA)".
3. **README**: assembled from `doc/*.rst` fragments by `oca-gen-addon-readme`.
4. **File layout**: standard, predictable.
5. **Code style**: enforced by `pre-commit` with `pylint-odoo`, `flake8`, `black`.
6. **Test coverage**: meaningful tests; no skipped tests without justification.
7. **i18n**: `i18n/<module>.pot` template + per-language `.po` files.

## Manifest checklist

```python
{
    "name": "Module Display Name",                      # Title Case, descriptive
    "version": "17.0.1.0.0",                            # see version rule
    "summary": "Short one-line description",            # ≤ 100 chars
    "author": "Original Author, Other Contributor, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/<repo-name>",    # the OCA repo, not the module
    "license": "AGPL-3",                                # or LGPL-3
    "category": "Standard Odoo Category",               # see /addons/base/data/ir_module_category_data.xml
    "depends": [
        # alphabetical, one per line
        "base",
        "hr",
        "mail",
    ],
    "data": [
        "security/...",
        "data/...",
        "views/...",
    ],
    "demo": ["demo/demo.xml"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "external_dependencies": {
        "python": ["python-stdnum"],
        "bin": ["wkhtmltopdf"],
    },
}
```

OCA-specific points:
- `author` must include "Odoo Community Association (OCA)" — this is what marks the module.
- `website` points to the OCA repo housing the module, not your personal site.
- `summary` is shown in app lists; spend time on it.

## Pre-commit configuration

Drop in `.pre-commit-config.yaml` at the repo root (one per OCA repo, not per module):

```yaml
exclude: |
  (?x)
  ^setup/|
  /static/(src/lib|description)/

repos:
  - repo: https://github.com/OCA/oca-addons-repo-template
    rev: 17.0
    hooks:
      - id: oca-gen-addon-readme
        args: [--repo-name=odoo-senior-engineer-pack, --branch=17.0]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-merge-conflict
      - id: mixed-line-ending

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.10

  - repo: https://github.com/PyCQA/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/PyCQA/flake8
    rev: 6.1.0
    hooks:
      - id: flake8

  - repo: https://github.com/OCA/pylint-odoo
    rev: v9.0.5
    hooks:
      - id: pylint_odoo
```

Then:
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## pylint-odoo highlights

`pylint-odoo` ships Odoo-specific checks. The categories most often hit:

| Check | What it catches |
|---|---|
| `manifest-required-author` | OCA author missing |
| `manifest-version-format` | Version not `17.0.X.Y.Z` |
| `missing-readme` | No README.rst |
| `missing-return` | Override missing `return super(...)` |
| `print-used` | `print()` left in code |
| `translation-required` | User-facing string not wrapped in `_()` |
| `attribute-deprecated` | Using `attrs=` / `states=` (deprecated in v17) |
| `sql-injection` | f-string in `cr.execute` |
| `external-request-timeout` | `requests.get/post` without `timeout=` |
| `no-write-in-compute` | Compute doing `record.write({...})` (anti-pattern) |
| `method-required-super` | Override of `create`/`write`/`unlink` not calling `super` |
| `xml-syntax-error` | Bad XML |
| `redefined-builtin` | Shadowing built-ins |

Run manually:
```bash
pylint --load-plugins=pylint_odoo -d all -e odoolint hr_overtime/
```

## README fragments

OCA modules don't write `README.rst`. They write fragments and let `oca-gen-addon-readme` build it:

```
doc/
├── description.rst       # 2-3 sentences: what does this do
├── configure.rst         # what to configure after install
├── usage.rst             # how to use it
├── ROADMAP.rst           # known limitations / future work
├── changelog.rst         # version history
├── credits.rst           # authors, contributors, sponsors, financial
└── installation.rst      # special install steps (rare)
```

Each fragment uses RST. Keep them short and direct — reviewers and users actually read them.

### `description.rst` example
```rst
This module adds approval workflows for employee overtime requests.
Employees submit overtime through their portal; managers approve
or refuse, with the approved hours flowing into payroll.
```

### `usage.rst` example
```rst
To submit overtime
~~~~~~~~~~~~~~~~~~

#. Open *HR > Overtime > My Requests*
#. Click *New*
#. Fill in date, hours, and justification
#. Click *Submit*

Your manager receives a notification and can approve from
*HR > Overtime > Pending Approval*.
```

## Versioning rule

`{odoo_version}.{major}.{minor}.{patch}` — for v17, that's `17.0.X.Y.Z`. Bump:
- Patch (Z): bugfixes only
- Minor (Y): new features, backward-compatible
- Major (X): breaking changes that need migration

A new module starts at `17.0.1.0.0`. The `17.0` prefix never changes within the v17 line.

## License headers

Each `.py` file starts with:
```python
# Copyright 2026 Jean Suarez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
```

XML files start with the same comment block:
```xml
<?xml version="1.0" encoding="utf-8"?>
<!-- Copyright 2026 Jean Suarez
     License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). -->
<odoo>
    ...
</odoo>
```

## Translations

```bash
# Generate the .pot template
odoo --modules=hr_overtime --i18n-export=hr_overtime/i18n/hr_overtime.pot --stop-after-init

# For a new locale
cp hr_overtime/i18n/hr_overtime.pot hr_overtime/i18n/es.po
# Edit es.po with translations, then commit both .pot and .po
```

`oca-port` and `Transifex` typically handle this in active OCA repos.

## CI checklist for OCA-style repo

- [ ] `pre-commit run --all-files` passes
- [ ] `pylint --load-plugins=pylint_odoo -e odoolint <addon>/` passes
- [ ] All Python files have license header
- [ ] All XML files have license comment
- [ ] `__manifest__.py` includes "Odoo Community Association (OCA)" in author
- [ ] `doc/` fragments present and accurate
- [ ] `i18n/<addon>.pot` regenerated and committed
- [ ] Version bumped following `17.0.X.Y.Z`
- [ ] Tests pass with `--test-enable`
- [ ] No `print()` / `breakpoint()` / `pdb` left in
- [ ] `static/description/icon.png` exists, 140×140

## Common pitfalls

- Editing `README.rst` directly — gets overwritten by `oca-gen-addon-readme`. Always edit fragments.
- License header missing on new files — reviewers will catch it; pre-commit can be configured to enforce.
- Author string says "OCA" instead of "Odoo Community Association (OCA)" — exact wording matters for tooling.
- `external_dependencies.python` listing packages that are already Odoo deps (like `requests`) — bloats the dependency graph.
- Forgetting `i18n/` directory entirely — translators can't contribute.
- Adding new dependencies in `depends=` to non-OCA / non-Odoo modules without justification — kills portability.
- Bumping version "17.1.0.0" instead of "17.0.1.0.0" — breaks the parser.

## References

- [OCA Contributing Guide](https://github.com/OCA/odoo-community.org/blob/master/website/Contribution/CONTRIBUTING.rst)
- [OCA maintainer-tools](https://github.com/OCA/maintainer-tools)
- [pylint-odoo](https://github.com/OCA/pylint-odoo)
- [oca-addons-repo-template](https://github.com/OCA/oca-addons-repo-template)
