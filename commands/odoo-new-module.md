---
name: odoo-new-module
description: Scaffold a new OCA-compliant Odoo 17 module
argument-hint: <module_name> [--license=AGPL-3] [--application]
---

You are scaffolding a new Odoo 17 module. Follow the OCA + Odoo official conventions exactly.

## Inputs

`$ARGUMENTS` — the module's technical name (snake_case, e.g. `hr_overtime`) and optional flags.

If no name was given, ask the user:
1. Module technical name (snake_case)
2. Display name (Title Case)
3. One-line summary (≤ 100 chars)
4. License (default: `AGPL-3`)
5. Is this an application? (default: no)
6. Top-level dependencies beyond `base` (e.g. `hr`, `mail`, `account`)

## Steps

Use the `module-scaffolding` skill as your reference for layout. Then:

1. Create the directory structure:
   ```
   <module_name>/
   ├── __init__.py
   ├── __manifest__.py
   ├── README.rst                        (or doc/ fragments if OCA)
   ├── data/
   ├── demo/
   ├── i18n/
   ├── models/__init__.py
   ├── controllers/__init__.py
   ├── views/
   ├── security/ir.model.access.csv      (with header, no rows yet)
   ├── static/description/icon.png       (placeholder note for the user)
   └── tests/__init__.py
   ```

2. Generate `__manifest__.py` with:
   - Version `17.0.1.0.0`
   - Author including "Odoo Community Association (OCA)" (only if user said it's OCA-style)
   - License from input
   - Empty `data` list (with comment listing the load order)
   - Stable `depends` from input
   - `installable: True`

3. Generate `models/__init__.py` empty (or with a sample import if user provided a model).

4. Generate `tests/__init__.py` empty.

5. Generate empty `security/ir.model.access.csv` with the correct header:
   ```csv
   id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
   ```

6. If OCA mode, generate `doc/description.rst`, `doc/usage.rst`, `doc/configure.rst`, `doc/credits.rst` skeletons.

7. Tell the user:
   - Where the module was created
   - That `static/description/icon.png` needs to be added (140×140)
   - Next steps: `/odoo-add-field` to start defining models, or open the manifest and edit by hand

## Quality bar

- Manifest is syntactically valid Python (a literal dict).
- Version follows `17.0.X.Y.Z`.
- All `__init__.py` files exist (Python won't load packages without them).
- ACL CSV exists even if empty — placeholder reminds the user to add ACLs when the first model is defined.
- File layout matches what `module-scaffolding` documents.

## What NOT to do

- Don't put fake/placeholder model code into `models/` — leave it empty so the user (or follow-up commands) can add real ones.
- Don't generate views without models — wait for the user to define a model first.
- Don't pick `application: True` unless the user explicitly said so — most modules are not applications.
- Don't add `mail.thread` to depends unless the user mentioned chatter — adding it surprises later.
