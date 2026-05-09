---
name: debugging-deep
description: Deep debugging of Odoo 17 — --dev=all flags, the Odoo Profiler, pg_stat_statements, query analysis with EXPLAIN, browser DevTools for OWL, log_handler scoping, remote debugging, and triage workflows. Use when basic checks failed and you need to diagnose performance, intermittent failures, or unclear errors.
---

# Debugging Deep Dive (Odoo 17)

## When to use this skill

The basic `/odoo-debug` checklist didn't solve it. You need to dig into actual SQL, profile a request, attach a debugger, or correlate browser-side and server-side traces.

## --dev= flags individually

`--dev=all` is the kitchen sink. The individual flags:

| Flag | What it does |
|---|---|
| `xml` | Reload XML on file change (no restart) |
| `qweb` | Reload QWeb on file change |
| `reload` | Reload Python on file change (autoreload) |
| `werkzeug` | Better error pages (Werkzeug debugger) |
| `assets` | Don't bundle JS/CSS (load each file individually for debug) |
| `tests` | Enable test routes |
| `pudb` / `pdb` / `ipdb` | Drop into respective debugger on uncaught exception |
| `all` | All of the above |

```bash
odoo --dev=xml,qweb,assets,reload -d mydb
odoo --dev=all -d mydb
```

In production: never `--dev=all`. The Werkzeug debugger gives an interactive Python console **on the error page**, accessible to anyone who triggers an error.

## The Odoo Profiler

Available in v17 with `--dev=all` (or with debug mode + admin). Records:
- SQL queries with timing
- Python calls with timing
- ORM operations

Activate from Settings > Technical > Profiling, or programmatically:

```python
from odoo.tools.profiler import Profiler

with Profiler(collectors=["sql", "traces_async"], db="mydb"):
    self.env["hr.overtime"].search([])._compute_something()
```

The profile is stored in `ir.profile` records. View them in Settings > Technical > Profile records, or download the speedscope JSON for visualization.

## SQL debugging

### Log every query
```bash
odoo -d mydb --log-handler=odoo.sql_db:DEBUG
```

You'll see:
```
[INFO] odoo.sql_db: query: SELECT id, name FROM res_partner WHERE active = true
[INFO] odoo.sql_db:   bad query: 0.123s elapsed, 1242 rows
```

### Scope to a specific module
```bash
odoo -d mydb --log-handler=odoo.addons.hr_overtime:DEBUG
```

### Postgres `pg_stat_statements`

Enable in `postgresql.conf`:
```
shared_preload_libraries = 'pg_stat_statements'
```

Then in psql:
```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Top 10 slowest queries
SELECT
    substring(query, 1, 100) AS short_query,
    calls,
    total_exec_time,
    mean_exec_time,
    rows
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;
```

Find the slow ones, run `EXPLAIN ANALYZE` on them, add indexes accordingly.

### EXPLAIN a specific query

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, name FROM hr_overtime
WHERE company_id = 1 AND state = 'submitted'
ORDER BY date DESC LIMIT 50;
```

Look for:
- `Seq Scan` on a large table → missing index
- `Hash Join` with large rows → consider denormalization or rule rewrite
- High `Buffers: read=...` → cold cache, may need to warm
- `Rows Removed by Filter:` huge → filter is post-fetch; index covers wrong columns

## ORM-level debugging

### What queries did this method run?
```python
import logging
_logger = logging.getLogger("odoo.sql_db")
_logger.setLevel(logging.DEBUG)

records.method_being_debugged()
```

### Drop into pdb
```python
import pdb; pdb.set_trace()
# Or for richer:
import pudb; pudb.set_trace()
```

Reaching this in worker mode hangs the worker; use single-thread (`workers = 0` in odoo.conf) for interactive debugging.

### Inspect cache state
```python
self.env.cache._data           # the raw cache dict
records._fields                # all field descriptors
records._cache                 # legacy cache reference
records.flush_recordset()      # force pending writes to DB
self.env.invalidate_all()      # nuke cache
```

## Browser-side (OWL / web client)

### Open browser DevTools → Sources tab

With `--dev=assets`, JS files load individually (not bundled), so breakpoints work.

### React-style component inspection

Add this once per session (in Console):
```js
odoo.__DEBUG__.services
odoo.__DEBUG__.services["orm"]
```

Inspect a specific component: open DevTools, click on the element, in Console:
```js
$0.__owl__.component         // the OWL component instance
$0.__owl__.component.state   // its reactive state
```

### Network panel

Look for `/web/dataset/call_kw` calls — those are ORM RPCs from the client. The payload tells you exactly what model/method/args were sent.

### OWL warnings

`onWillStart` errors, missing props, missing template — appear in the Console as red errors. Address them; they're not just warnings.

## Remote debugging (production-safe-ish)

### Read-only `odoo shell`

```bash
ssh user@server "cd /opt/odoo && ./odoo-bin shell -d production_db"
>>> self.env["hr.overtime"].search([], limit=5)
>>> self.env["res.partner"].browse(123).read(["name", "email"])
```

`shell` gives you a Python REPL with `self` set to a recordset. Read-only by convention — don't write unless you mean it.

### Read replicas
For analytics or heavy reporting, configure a Postgres read replica and point read-only Odoo workers at it. Configure with `db_replica_host`, `db_replica_port` in `odoo.conf` (v17 supports replica routing for SELECT).

### Query a production DB without going through Odoo

```bash
psql -h db.host -U readonly_user production_db -c "
  SELECT state, COUNT(*) FROM hr_overtime GROUP BY state;
"
```

A read-only Postgres user is safer than running `odoo shell`.

## Log strategy in production

### Default
```ini
log_level = info
log_handler = :INFO
```

### Scope debug to one module without spamming
```ini
log_handler = :INFO,odoo.addons.hr_overtime:DEBUG
```

### Slow query logging at Postgres level
In `postgresql.conf`:
```
log_min_duration_statement = 500   # log queries > 500ms
log_statement = none                # otherwise too noisy
```

## Triage by symptom

### "Worker silently hangs"
- Likely: outbound HTTP without timeout, infinite loop, deadlock on a record
- Find: `ps aux | grep odoo` shows worker stuck; `py-spy dump --pid <pid>` shows the Python stack
- Fix: timeout on requests, audit the loop, reduce lock scope

### "Random 502 from nginx"
- Worker dying. Check `/var/log/odoo/odoo.log` for `Out of memory` or `worker killed`.
- Raise `limit_memory_hard` or find the memory leak.

### "Tests pass locally, fail in CI"
- Different DB state. CI starts from empty; local has accumulated data.
- Use `setUpClass` to create everything the test needs; never rely on `--demo` data.

### "User says 'I get an error sometimes'"
- Get the **exact** time. Correlate with `odoo.log` and `nginx access log` at that timestamp.
- Look for tracebacks just before the user complaint.

### "Compute sometimes wrong"
- Missing `@api.depends` for a field that affects the result. The recompute happens, but the depends graph doesn't know to trigger.
- Or: the compute writes to a different record (forbidden, breaks the cache).
- Add `_logger.info` in the compute showing which records and inputs.

### "Slow under load, fast in dev"
- Index on `company_id`? Multi-company rule does `IN (1)` join — needs index.
- `_order` field indexed?
- `pg_stat_statements` will show which query dominates.

### "Random AccessError"
- Probably a record rule referencing a field that's NULL for some records.
- Reproduce: `record.with_user(failing_user).check_access_rule("read")` to get the exact rule that denies.

## Tools cheat sheet

| Need | Tool |
|---|---|
| What's this Python doing right now? | `py-spy dump --pid <pid>` |
| Profile a request | Odoo Profiler with `--dev=all` |
| Why is this query slow? | `EXPLAIN ANALYZE` |
| What queries did the request run? | `--log-handler=odoo.sql_db:DEBUG` |
| What's in the ORM cache? | `self.env.cache._data` (dev only) |
| OWL component state | `$0.__owl__.component.state` in DevTools |
| Read prod safely | Read replica + read-only psql user |

## Common pitfalls

- Running `--dev=all` in production "just for an hour to debug" → security hole.
- `pg_stat_statements` not enabled → flying blind on prod query patterns.
- Logging credentials at DEBUG level → secrets in log files.
- Adding `_logger.debug()` to every method → log volume explodes; use module-scoped log levels.
- Using `time.time()` to measure ORM operations → misleading because of caching/prefetch. Use the Profiler.
- `pdb.set_trace()` left in committed code → CI hangs.

## References

- [Odoo 17 — Developer mode and tools](https://www.odoo.com/documentation/17.0/applications/general/developer_mode.html)
- [Odoo 17 — Performance optimisation](https://www.odoo.com/documentation/17.0/administration/on_premise/source.html)
- [pg_stat_statements](https://www.postgresql.org/docs/current/pgstatstatements.html)
- [py-spy](https://github.com/benfred/py-spy)
