---
name: odoo-profile
description: Profile a slow Odoo 17 method, view, or report. Walk through enabling the Profiler, capturing a trace, identifying SQL/Python hotspots, and proposing optimizations.
argument-hint: [method_name_or_url_or_view]
---

You are profiling a slow Odoo operation. Use the `debugging-deep` and `performance` skills as references.

## Inputs

`$ARGUMENTS` — what's slow. Method name, view name, URL, or "the list view of X".

If unclear, ask:
1. What action is slow? (open list, open form, click button, run report, save)
2. How slow? (seconds at low data, seconds at production data)
3. Same slow on dev vs prod? Or only with real data volumes?
4. Dev DB available with realistic data?

## Steps

1. **Reproduce** — make sure you can repro on a controllable env (dev or staging with prod-sized data).

2. **Capture a profile**:
   ```python
   from odoo.tools.profiler import Profiler
   with Profiler(collectors=["sql", "traces_async"], db=self.env.cr.dbname):
       self.env["my.model"].slow_method()
   ```
   Or run with `--dev=all` and use Settings > Technical > Profiling.

3. **Identify the dominant cost**:
   - SQL: which query? How many calls?
   - Python: which method?
   - ORM cache invalidation: many small reads after each write?

4. **Run EXPLAIN** on the dominant SQL query.

5. **Diagnose** based on the pattern:
   - Many small queries → N+1 or missing prefetch
   - One huge query → missing index or unstored compute in the domain
   - High Python self-time → inefficient algorithm or bad recordset usage
   - High write count → unbatched writes or redundant `flush_recordset`

6. **Propose fixes** in priority order:
   - Add `index=True` on FK / domain field
   - Convert compute to `store=True` (with right `@api.depends`)
   - Use `_read_group` instead of Python-side aggregation
   - Batch writes
   - Move expensive logic to a `queue_job`

7. **Measure again** — confirm the fix actually moved the needle.

## Output

```markdown
## Profile of: <operation>

### Setup
- Env: <dev / staging>
- Data volume: <N records>
- Reproduction steps: <click sequence / RPC call>

### Hotspots (top 5 by cost)
| Rank | Cost | What | Cause hypothesis |
|---|---|---|---|

### Dominant SQL
```sql
<the query>
```

### EXPLAIN ANALYZE
```
<plan>
```

### Diagnosis
<Concise: this is N+1 because…, this is missing index because…, this is unstored compute because…>

### Proposed fixes
| Priority | Change | Expected gain | Effort |
|---|---|---|---|

### Verification plan
1. Apply fix
2. Re-run profile on same data
3. Compare timings: was X ms, now Y ms

### Side effects to check
- [ ] Existing tests still pass
- [ ] Stored compute correct on existing records (migration may be needed)
- [ ] Index doesn't bloat insert-heavy paths
- [ ] Queue job retries don't cascade
```

## Quality bar

- Always show **measured** numbers. "It feels slow" is not a profile.
- One fix at a time. Measure between fixes.
- Don't add an index without confirming it's actually used (`EXPLAIN`).
- Don't convert compute to `store=True` without auditing every dependency tracked field.
- Document the new performance expectation so it's verifiable later.

## What NOT to do

- Don't optimize blindly. Profile first.
- Don't propose 10 fixes at once.
- Don't add caching without invalidation logic.
- Don't `sudo()` to skip rules — that's not a perf optimization, that's a security regression.
