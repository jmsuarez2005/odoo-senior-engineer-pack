---
name: performance
description: Optimize Odoo 17 performance — prefetch, N+1 avoidance, store= on computes, indexes, query profiling, flush_model. Use when investigating slow views, slow reports, slow imports, or planning performance for a new model.
---

# Performance (Odoo 17)

## When to use this skill

A list view loads slowly. A report takes minutes. An import script crawls. A search returns timeout. You want to design a new model that won't have these problems.

## The mental model

Odoo's ORM is **batch-friendly by default** — but only if you don't fight it. Performance problems almost always come from one of:

1. **N+1 queries** — looping over records and triggering one query per record
2. **Missing index** — domains/orders/group-bys hitting unindexed columns
3. **Unstored computes** in domains/group-bys — recomputed on every query
4. **Excessive cache invalidation** — tight write loops dropping prefetched data
5. **Cartesian explosions** — Many2many joins without filters

## Prefetching — Odoo's superpower

When you read a field on a recordset of N records, Odoo fetches that field for **all N** at once. Don't break this.

```python
# GOOD — one SQL per field, regardless of N
partners = self.env["res.partner"].search([])
for p in partners:
    print(p.name, p.email, p.country_id.name)
# 3 queries total: partners, countries, (display_name fields)

# BAD — defeats prefetch
for partner_id in partner_ids:
    p = self.env["res.partner"].browse(partner_id)
    print(p.name)  # one query PER iteration
```

The fix when you have a list of IDs:
```python
# Browse all at once → recordset preserves prefetch
partners = self.env["res.partner"].browse(partner_ids)
for p in partners:
    print(p.name)
```

## `store=True` on computes

A computed field that's **read frequently** or used in **domains, order, or group-by** should usually be stored.

```python
# Unstored — recomputed every time it's read
total = fields.Float(compute="_compute_total")

# Stored — computed once on write, cached in DB
total = fields.Float(compute="_compute_total", store=True)
```

Stored computes:
- Cost a write when dependencies change (`@api.depends` triggers a recompute)
- Are searchable (you can filter `total > 100` in domains)
- Are sortable (`_order = "total desc"` works)
- Pay for themselves in seconds when read in lists

Unstored computes are right when:
- Read rarely (e.g., only on form view of a single record)
- Depends on `self.env.user` or other context
- The compute is cheap (< 1ms)

## Indexes

`index=True` on a field tells Odoo to add a Postgres B-tree index. Add it on:

- Foreign keys you query frequently in domains
- Fields used in `_order`
- Fields used in heavy `groupby`
- Fields used in `search` from large tables

```python
employee_id = fields.Many2one("hr.employee", index=True)
state = fields.Selection([...], index=True)
date = fields.Date(index=True)
```

For multi-column queries (`WHERE company_id = X AND state = 'draft'`), a composite index helps. Add via SQL in `__init__.py`:

```python
def _auto_init(self):
    res = super()._auto_init()
    self.env.cr.execute("""
        CREATE INDEX IF NOT EXISTS hr_overtime_company_state_idx
        ON hr_overtime (company_id, state)
        WHERE state IN ('submitted', 'approved')
    """)
    return res
```

(Partial index — only the rows you actually query.)

## Read groups (the heart of dashboards)

```python
totals = self.env["hr.overtime"].read_group(
    domain=[("date", ">=", "2026-01-01")],
    fields=["hours:sum"],
    groupby=["employee_id"],
    orderby="hours desc",
    limit=10,
)
# returns: [{"employee_id": (1, "Foo"), "hours": 240.0, "__count": 12}, ...]
```

`read_group` does aggregation in Postgres. Don't replicate this in Python.

For more complex aggregation, use `_read_group` (the v17 lower-level API) which returns tuples and is more flexible.

## Search optimizations

```python
# Limit + order = use the right index
self.env["res.partner"].search([("active", "=", True)], limit=10, order="create_date desc")

# search_count is faster than len(search(...))
n = self.env["res.partner"].search_count([("active", "=", True)])

# Direct ID-only search for chained operations
ids = self.env["res.partner"].search([("active", "=", True)]).ids

# search_read fetches in one query (search + read)
data = self.env["res.partner"].search_read(
    [("active", "=", True)],
    ["name", "email"],
    limit=100,
)
```

## Bulk write vs loop

```python
# GOOD — single UPDATE
records.write({"state": "approved"})

# BAD — N UPDATEs + N cache invalidations
for record in records:
    record.state = "approved"
```

Same for create:
```python
# GOOD — batched create (uses @api.model_create_multi)
self.env["hr.overtime"].create([
    {"employee_id": e.id, "hours": h} for e, h in zip(emps, hours_list)
])

# BAD
for e, h in zip(emps, hours_list):
    self.env["hr.overtime"].create({"employee_id": e.id, "hours": h})
```

## Avoiding cache flush thrash

Each `write` invalidates the cache for affected fields. In tight loops, this costs more than it should.

```python
# If you'll write to a recordset many times, flush at the end
for record in records:
    record.compute_something()
# All the writes batched in cache; flush once before reading downstream
self.env.flush_all()
```

For deeper control:
- `record.flush_recordset(["field"])` — flush specific fields
- `self.env.invalidate_all()` — drop all caches (use sparingly)

## Computing expensive things lazily

If a compute is expensive but rarely needed:

```python
@api.depends_context("compute_expensive")
def _compute_huge_thing(self):
    if not self.env.context.get("compute_expensive"):
        for record in self:
            record.huge_thing = 0
        return
    # ... real computation
```

Then trigger only when needed: `record.with_context(compute_expensive=True).huge_thing`.

## Profiling

### Server-side
```bash
# Run with profiler enabled, then watch the log
odoo --dev=all -d mydb
```

Use the Profiler from Settings > Technical (must be enabled in `--dev=all`). Records SQL, Python, and JS trace data.

### Specific request
```python
from odoo.tools.profiler import Profiler
with Profiler():
    self.env["hr.overtime"].search([])  # whatever you're profiling
```

### SQL queries logged
```bash
odoo -d mydb --log-sql
# or
odoo -d mydb --log-handler=odoo.sql_db:DEBUG
```

## Common patterns

### Stat button without N+1
```python
overtime_count = fields.Integer(compute="_compute_overtime_count")

def _compute_overtime_count(self):
    counts = dict(self.env["hr.overtime"].read_group(
        [("employee_id", "in", self.ids)],
        ["employee_id"],
        ["employee_id"],
    ))
    counts = {c["employee_id"][0]: c["employee_id_count"] for c in counts}
    for employee in self:
        employee.overtime_count = counts.get(employee.id, 0)
```

### Cron-friendly batch processing
```python
def _cron_process_overtimes(self, batch_size=500):
    domain = [("state", "=", "submitted"), ("processed", "=", False)]
    while True:
        records = self.env["hr.overtime"].search(domain, limit=batch_size)
        if not records:
            break
        records._do_processing()
        self.env.cr.commit()  # commit each batch — long crons should not hold one tx
```

`self.env.cr.commit()` releases locks and lets concurrent users work. Only OK in cron / standalone scripts, never inside a request handler.

## Anti-patterns

- **`for record in records: do_thing(record)` when `do_thing` writes** — each iteration triggers a write + cache invalidation. Batch instead.
- **Using `mapped("o2m_field.x")` over huge recordsets** — fetches all child records into memory. Use `read_group` or paginate.
- **`search([("computed_field", ">", x)])` where `computed_field` is unstored** — Odoo can't translate to SQL, falls back to in-memory eval over the whole table.
- **`sudo()` to "make a query faster"** — sudo bypasses ACL checks but doesn't make SQL faster. The slow part is rules; consider rewriting them.
- **`for r in records: r.flush_recordset()`** — flushing per-record is the opposite of batching.

## Multi-company performance

Multi-company record rules add `company_id IN (...)` to every query. Make sure `company_id` is **indexed** on every multi-company model. Without it, every list view with multi-company users does a full table scan.

## Database advice

- Postgres `EXPLAIN ANALYZE` is your friend for slow queries.
- `pg_stat_statements` extension shows top-N slowest queries. Enable in production.
- `_order` becomes `ORDER BY` on every default query — match it with an index.

## Common pitfalls

- Index on `name` field forgotten when users search by name → slow autocomplete.
- Using `mapped("partner_id.country_id.name")` with N partners → 3 queries thanks to prefetch (good!) but only if `partners` is a single recordset. Iterating manually breaks it.
- `compute=` set without `@api.depends` → recomputed on every read (Odoo logs a warning, but easy to miss).
- Tests pass with empty DB but production hangs → benchmark with realistic data volumes.
- Adding `index=True` after a model has millions of rows → migration adds the index online but takes long; do it during a maintenance window.
- Storing huge HTML/Text fields directly on a frequently-listed model → list view fetches them. Move to a separate model or `attachment=True`.

## References

- [Odoo 17 — Performance](https://www.odoo.com/documentation/17.0/developer/reference/backend/queries.html)
- [Odoo 17 — ORM cache](https://www.odoo.com/documentation/17.0/developer/reference/backend/orm.html#flush)
