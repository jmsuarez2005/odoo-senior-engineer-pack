---
name: odoo-debug
description: Debugging checklist and triage for Odoo 17 issues — install errors, runtime errors, view loading, slow performance
argument-hint: [error_message_or_symptom]
---

You are debugging an Odoo 17 issue. Be methodical: identify the layer, narrow the cause, verify the fix.

## Inputs

`$ARGUMENTS` — optional symptom or error. If absent, ask:
1. What's the symptom? (error message, slow operation, unexpected behavior)
2. When does it happen? (install / upgrade / runtime / specific action)
3. What changed recently? (new module, upgrade, infra change)

## The triage tree

### Step 1: Identify the layer

| Symptom | Likely layer |
|---|---|
| `External ID not found` | XML data load order |
| `psycopg2.errors.NotNullViolation` | Required field missing during install/migration |
| `AccessError: ...` | ACL / record rule |
| `KeyError: 'view_id'` or similar | View XML / inheritance |
| Stat button shows "0" but DB has rows | Compute / prefetch / multi-company |
| 502 from nginx | Worker died (memory) or longpolling not proxied |
| Slow list view | Missing index / unstored compute |
| OWL component blank | Asset bundle missing template / JS path |

### Step 2: Read the actual error

```bash
# Ensure you're seeing real-time logs with full info
odoo --dev=all -d <db>
# OR for systemd
sudo journalctl -u odoo -f
```

`--dev=all` enables:
- Reload on file change
- XML / asset reload without restart
- Detailed error pages
- Profiler available

Read the **full traceback**, not just the last line. The "caused by:" chains often point to the real culprit.

### Step 3: Common-cause checklist by symptom

#### `External ID not found in the system: my_module.foo`
- The XML record `foo` doesn't exist or is loaded **after** this reference.
- Check `data` order in `__manifest__.py` — security first, then data, then views.
- Check the `ref=` is correct (typos, missing module prefix).

#### `Field 'X' does not exist`
- The field was added but the module wasn't upgraded. Run `odoo -u <module>`.
- Or the field is on a parent class but the inheritance chain is wrong (`_inherit` vs `_inherits`).

#### `AccessError: You are not allowed to modify ...`
- No row in `ir.model.access.csv` for the user's group → no access at all.
- Row exists but `perm_write=0` → has read but not write.
- Record rule denies it → check `domain_force` evaluation against the user.
- Reproduce: `record.with_user(user_id).check_access_rights('write')` and `check_access_rule('write')`.

#### `psycopg2.errors.NotNullViolation` on upgrade
- New required field added to a model that has existing rows.
- Fix: add a `default=` (works for new rows) AND a `migrations/<v>/post-migration.py` that backfills.

#### Compute returns wrong value
- Missing `@api.depends` for one of the inputs → not recomputed when input changes.
- Compute reads `self.env.context` but missing `@api.depends_context`.
- Compute writes to a record outside `self` → forbidden, breaks cache invariants.

#### Slow list view
- Check the `_order` — does it have an index?
- Are any displayed fields unstored computes?
- Domain on a column without an index?
- Multi-company `company_id` indexed?
- Run `odoo --log-sql -d <db>` to see queries.

#### OWL component not rendering
- Missing `/** @odoo-module **/` at top of JS file.
- XML template not in any asset bundle.
- Component registered to wrong category.
- Check browser console — likely an import error.

#### 502 / worker dying
- Check `journalctl -u odoo` for OOM kills.
- Memory limit too low for the workload (raise `limit_memory_hard`).
- Long-running request hitting `limit_time_real` — chunk the work or raise the limit.

### Step 4: Verify, don't assume

After applying a fix:
- **Reproduce** the original error to confirm it was the right fix.
- Run the test suite scoped to the module: `odoo -d testdb -u <module> --test-enable --test-tags=<module>`.
- Smoke-test the user flow.

## Useful debugging tools

```python
# Drop into pdb at a specific point
import pdb; pdb.set_trace()

# Log inside a method
import logging
_logger = logging.getLogger(__name__)
_logger.info("State: %s", record.state)
```

```bash
# Test the queries a method runs
odoo shell -d <db>
>>> self.env["hr.overtime"].search([])
>>> # Check what's actually in the DB
>>> self.env.cr.execute("SELECT id, name, state FROM hr_overtime")
>>> self.env.cr.fetchall()
```

```bash
# Re-run install/upgrade
odoo -d <db> -u <module> --stop-after-init
odoo -d <db> -i <module> --stop-after-init       # fresh install
```

## Output format

When the user gives a symptom, produce:

1. **Hypothesis** — likely cause based on the layer + symptom
2. **Verify** — concrete commands or checks to confirm
3. **Fix** — what to change
4. **Test** — how to verify the fix
5. **Prevent** — what convention/check would have caught this earlier

If the symptom is too vague, ask **one** focused question to narrow it.

## What NOT to do

- Don't suggest `sudo()` to "make the error go away" — find the real cause.
- Don't reinstall modules in production without backing up.
- Don't blindly run `--upgrade=all` — surface the specific module.
- Don't assume the user already tried the obvious things; ask.
