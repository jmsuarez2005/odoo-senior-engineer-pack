# Minimal Example Module

The smallest meaningful Odoo 17 module:
- One model (`minimal.book`)
- A computed stored field (`is_thick`)
- ACL for `base.group_user`
- List + form views
- One simple test

## Install

```bash
odoo -d test_db -i minimal_module --test-enable --stop-after-init
```

## What it shows

- Correct manifest structure
- License header on every file
- ACL CSV with the right header
- v17 view syntax (`<list>`, no `attrs=`)
- Basic compute with `@api.depends` and `store=True`
- Tagged test using `TransactionCase`

Use this as a starting template when scaffolding new modules.
