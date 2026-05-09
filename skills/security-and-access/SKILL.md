---
name: security-and-access
description: Configure Odoo 17 security — ir.model.access.csv, record rules (ir.rule), groups, sudo() vs with_user(), check_access_rights/check_access_rule. Use when adding ACLs, defining row-level rules, multi-company isolation, or auditing security on a model.
---

# Security & Access (Odoo 17)

## When to use this skill

Anything in `security/`. ACLs, record rules, groups, multi-company, or any time you're adding a new model and need to wire up its security story.

## The four layers

1. **Authentication** — handled by `res.users` / login flow. Almost never customized.
2. **Groups** — bags of permissions. Users belong to groups.
3. **Access rights (`ir.model.access`)** — model-level CRUD per group.
4. **Record rules (`ir.rule`)** — row-level filtering (which records of the model can a group see/edit).

A user can do an action only if **all four** allow it.

## Groups (`security_groups.xml`)

```xml
<odoo>
    <data noupdate="1">

        <record id="module_category_hr_overtime" model="ir.module.category">
            <field name="name">Overtime</field>
            <field name="description">Overtime module</field>
            <field name="sequence">30</field>
        </record>

        <record id="group_overtime_user" model="res.groups">
            <field name="name">User</field>
            <field name="category_id" ref="module_category_hr_overtime"/>
            <field name="comment">Can submit and view their own overtime.</field>
        </record>

        <record id="group_overtime_manager" model="res.groups">
            <field name="name">Manager</field>
            <field name="category_id" ref="module_category_hr_overtime"/>
            <field name="implied_ids" eval="[(4, ref('group_overtime_user'))]"/>
            <field name="comment">Can approve/refuse overtime, see all employees.</field>
        </record>

    </data>
</odoo>
```

Key things:
- `noupdate="1"` so re-installs don't reset user assignments.
- `implied_ids` — Manager *implies* User, so being Manager auto-grants User membership.
- `category_id` makes the group appear in the user form's Settings tab as a radio button (when category has multiple groups, user picks one — implied groups handle the hierarchy).

## Access rights (`ir.model.access.csv`)

CSV header (exact, in order):

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
```

Example:
```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_hr_overtime_user,hr.overtime.user,model_hr_overtime,hr_overtime.group_overtime_user,1,1,1,0
access_hr_overtime_manager,hr.overtime.manager,model_hr_overtime,hr_overtime.group_overtime_manager,1,1,1,1
```

Rules:
- `model_id:id` is `model_<table_with_underscores>` for the model in this module, or `<module>.model_<...>` for one in another module. So `hr.overtime` becomes `model_hr_overtime`.
- One row per (model × group). Add a row per group that needs access.
- Groups with no row = no access. Models with no row at all = only `base.group_system` (technical settings) can use them. **This is the most common security bug** — model created, ACL forgotten, only admin can use it.
- `perm_unlink=1` is rare. Most business records should be archivable (`active=False`) instead of deletable.

## Record rules (`record_rules.xml`)

Filter which **rows** a group can access.

```xml
<odoo>
    <data noupdate="1">

        <!-- Users see only their own overtime -->
        <record id="rule_hr_overtime_user" model="ir.rule">
            <field name="name">Overtime: User sees own only</field>
            <field name="model_id" ref="model_hr_overtime"/>
            <field name="groups" eval="[(4, ref('group_overtime_user'))]"/>
            <field name="domain_force">[('employee_id.user_id', '=', user.id)]</field>
            <field name="perm_read" eval="True"/>
            <field name="perm_write" eval="True"/>
            <field name="perm_create" eval="True"/>
            <field name="perm_unlink" eval="True"/>
        </record>

        <!-- Managers see all overtime in their company -->
        <record id="rule_hr_overtime_manager" model="ir.rule">
            <field name="name">Overtime: Manager sees company</field>
            <field name="model_id" ref="model_hr_overtime"/>
            <field name="groups" eval="[(4, ref('group_overtime_manager'))]"/>
            <field name="domain_force">[('company_id', 'in', company_ids)]</field>
        </record>

        <!-- Multi-company global rule (no groups = applies to everyone) -->
        <record id="rule_hr_overtime_company" model="ir.rule">
            <field name="name">Overtime: multi-company</field>
            <field name="model_id" ref="model_hr_overtime"/>
            <field name="global" eval="True"/>
            <field name="domain_force">[('company_id', 'in', company_ids)]</field>
        </record>

    </data>
</odoo>
```

### Domain variables you can use in `domain_force`

| Variable | Meaning |
|---|---|
| `user.id` | Current user ID |
| `user.partner_id.id` | Current user's partner |
| `user.company_id.id` | Active company |
| `company_ids` | List of allowed companies (multi-company-aware) |
| `time` | The Python time module |

### Group rules vs global rules

- **Group rule**: applies only to members of the listed groups, **OR-combined** with other group rules they qualify for.
- **Global rule** (`global=True`, no groups): applies to **everyone**, **AND-combined** with all group rules.

This is the source of subtle security bugs: a permissive group rule can be overridden by a restrictive global rule, and vice versa.

## `sudo()` — when and why

`record.sudo()` returns a copy of the recordset that bypasses ACL and record rules. **It is a trust boundary**.

Use it when:
- Reading a record the user shouldn't directly access, but business logic needs (e.g., updating an internal counter on a related record).
- A controller endpoint exposes a public action (e.g., portal accept).
- A scheduled cron needs to act across companies.

Don't use it when:
- You hit a permission error and don't understand why — debug instead.
- You're in a test and want to skip security setup — set up the right user instead.
- You're "just simplifying."

Document **every** `sudo()` with a comment explaining the trust boundary:

```python
# sudo: the portal user can't directly write res.partner, but accepting
# the quotation requires updating partner.signed_quote_count.
self.partner_id.sudo().signed_quote_count += 1
```

## `with_user(user)` vs `sudo()`

- `sudo()` — runs as superuser, bypassing all checks.
- `with_user(user)` — runs as `user`, enforcing **their** ACLs and rules.

Use `with_user` when you want to check "would this user be allowed?" without escalating. Common for delegated actions.

## Manual checks

```python
self.check_access_rights("write")  # raises AccessError if group ACL forbids
self.check_access_rule("write")    # raises AccessError if record rule forbids
self.check_access_rights("write", raise_exception=False)  # returns bool
```

Use these in custom controllers or unusual flows where the ORM doesn't auto-check (e.g., aggregating data across models).

## Multi-company

Best practices:
- Every business model has `company_id = fields.Many2one("res.company", ...)`.
- Add a global record rule limiting visibility to `company_ids`.
- Set `_check_company_auto = True` on the model — Odoo auto-validates that related fields' companies match.
- Use `check_company=True` on Many2one fields to specific other multi-company models.

```python
class HrOvertime(models.Model):
    _name = "hr.overtime"
    _check_company_auto = True

    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    employee_id = fields.Many2one("hr.employee", required=True, check_company=True)
```

## Controllers and endpoints

Public endpoints have a different default trust posture. The `auth=` param on `@http.route`:

| `auth` | Who can call | Implication |
|---|---|---|
| `user` | Logged-in users | Default for backend |
| `public` | Anyone | Apply tight checks; treat all input as untrusted |
| `none` | Anyone | No DB cursor; for static-ish endpoints |
| `bearer` | API token holders | Common for REST APIs |

Inside `auth="public"`, you typically operate on `request.env["model"].sudo()` — but always validate input first.

## Common pitfalls

- New model, no `ir.model.access.csv` row → "Sorry, you are not allowed to access" for non-admin users.
- `domain_force` referencing a field that doesn't exist on the model → silent SQL error during evaluation.
- `noupdate="1"` missing from `security_groups.xml` → upgrades reset implied groups, breaking permissions.
- Using `sudo()` and then writing user-supplied data without validation → privilege escalation.
- Multi-company rule with `domain_force="[('company_id', '=', company_id)]"` (singular) — that's not a valid variable. Use `company_ids` (plural).
- Adding ACL only for `group_overtime_manager` and forgetting `group_overtime_user` → users can't do anything.
- Putting `groups="..."` on a form button as the only check → backend method still callable via RPC.

## Audit checklist for a new model

- [ ] `ir.model.access.csv` entry per group that should have access
- [ ] Record rule for row-level filtering if business logic requires
- [ ] `company_id` field + global multi-company rule (if multi-company-relevant)
- [ ] `_check_company_auto = True` (if has cross-company FKs)
- [ ] `sudo()` calls in code each have a comment explaining trust boundary
- [ ] Controllers have explicit `auth=` matching intent
- [ ] No `cr.execute` reads bypassing ACL without explicit reasoning

## References

- [Odoo 17 — Security](https://www.odoo.com/documentation/17.0/developer/reference/backend/security.html)
- [Odoo 17 — Multi-company](https://www.odoo.com/documentation/17.0/applications/general/companies.html)
