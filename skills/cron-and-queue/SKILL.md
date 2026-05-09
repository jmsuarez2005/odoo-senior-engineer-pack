---
name: cron-and-queue
description: Build Odoo 17 scheduled jobs (ir.cron) and asynchronous job queues (OCA queue_job). Use when scheduling recurring tasks, processing things asynchronously, decoupling slow operations from user requests, batching imports/exports, or designing for retries and failure isolation.
---

# Cron & Job Queue (Odoo 17)

## When to use this skill

Recurring tasks, slow operations that shouldn't block users, batch processing, retry-able workflows, integrations with external systems.

## Two tools, two purposes

| Tool | Best for |
|---|---|
| `ir.cron` | Recurring scheduled tasks (every N minutes/hours/days), idempotent, low-medium volume |
| OCA `queue_job` | Async one-off jobs triggered by code, retries, parallelism, dependencies between jobs |

Use `ir.cron` when "do X every Y". Use `queue_job` when "this user action triggers a long task; let me run it in background and tell the user when done."

## ir.cron — scheduled jobs

### Define in XML data

```xml
<odoo>
    <data noupdate="1">
        <record id="cron_overtime_reminder" model="ir.cron">
            <field name="name">HR Overtime: Reminder for pending approvals</field>
            <field name="model_id" ref="model_hr_overtime"/>
            <field name="state">code</field>
            <field name="code">model._cron_remind_pending()</field>
            <field name="interval_number">1</field>
            <field name="interval_type">days</field>
            <field name="numbercall">-1</field>
            <field name="active" eval="True"/>
            <field name="user_id" ref="base.user_root"/>
            <field name="priority">10</field>
        </record>
    </data>
</odoo>
```

### Implement the method

```python
class HrOvertime(models.Model):
    _inherit = "hr.overtime"

    @api.model
    def _cron_remind_pending(self):
        """Send reminders for overtime pending > 3 days."""
        cutoff = fields.Datetime.now() - timedelta(days=3)
        pending = self.search([
            ("state", "=", "submitted"),
            ("create_date", "<", cutoff),
        ])
        for record in pending:
            record.activity_schedule(
                "mail.mail_activity_data_todo",
                summary=_("Overtime pending review"),
                user_id=record.employee_id.parent_id.user_id.id,
            )
```

### Cron rules

- **Idempotent**: cron may run twice (manual trigger + scheduled, or after a reboot). Design so re-running is safe.
- **No assumed user**: by default `user_id=base.user_root` (admin). If you need company context, set it explicitly.
- **Long crons**: don't hold one transaction. Commit periodically:
  ```python
  for batch in batches:
      batch._do_work()
      self.env.cr.commit()  # only inside cron / standalone
  ```
- **`numbercall=-1`**: run forever. `numbercall=N`: run N times then disable.
- **Concurrent crons on same DB**: one job runs at a time per cron. Different cron records can run in parallel (limited by `max_cron_threads` in `odoo.conf`).
- **Tag with `_logger`**: every cron should log start/end/counts so ops can verify it ran.

### Manual trigger / debugging

Settings > Technical > Scheduled Actions > pick yours > "Run Manually" button. Logs go to the regular Odoo log.

## OCA queue_job — async with retries

`queue_job` is an OCA module (`oca/queue`) that adds a Postgres-backed job queue. Each job is a row in `queue.job` with state, args, retries, dependencies.

### Install

```python
# __manifest__.py
"depends": ["queue_job"],
```

Plus a worker process — `queue_job` ships its own runner.

### Decorate methods

```python
from odoo.addons.queue_job.job import job

class HrOvertime(models.Model):
    _inherit = "hr.overtime"

    @job(default_channel="root.payroll")
    def send_to_payroll(self):
        """Push approved overtime to external payroll system."""
        self.ensure_one()
        response = requests.post(
            self.env["ir.config_parameter"].sudo().get_param("payroll.api_url"),
            json={"ref": self.name, "hours": self.hours},
            timeout=10,
        )
        response.raise_for_status()
        self.payroll_ref = response.json()["ref"]
```

### Enqueue from code

```python
def action_approve(self):
    super().action_approve()
    for record in self:
        record.with_delay(priority=10, max_retries=5).send_to_payroll()
```

`with_delay()` returns immediately; the job runs asynchronously. The user sees "Approved" instantly while payroll integration happens in background.

### Retries and exponential backoff

```python
from odoo.addons.queue_job.exception import RetryableJobError

@job
def call_flaky_api(self):
    try:
        return requests.post(URL, timeout=5)
    except requests.Timeout:
        raise RetryableJobError("API timeout, retrying", seconds=60)
```

`RetryableJobError` re-queues the job with a delay. Distinguishes from regular exceptions (which mark as failed).

### Dependencies between jobs

```python
job1 = self.with_delay().step1()
self.with_delay(depends_on=job1).step2()
```

`step2` won't run until `step1` succeeds.

### Channels for parallelism control

Configure in `odoo.conf`:
```ini
[queue_job]
channels = root:1,root.payroll:5,root.heavy:1
```

- `root:1` — default channel, 1 worker
- `root.payroll:5` — payroll channel allows 5 concurrent
- `root.heavy:1` — single-threaded for resource-intensive work

### Monitoring

`queue.job` view shows pending, started, done, failed jobs. Failed ones can be retried manually or auto-archived.

## Patterns

### Batch import / export
```python
@job
def import_chunk(self, file_url, offset, limit):
    # Fetch chunk N of N from a URL
    ...

def trigger_full_import(self, file_url, total):
    chunk = 500
    for offset in range(0, total, chunk):
        self.with_delay(priority=20).import_chunk(file_url, offset, chunk)
```

### Webhook receiver → queue
```python
@http.route("/webhook/foo", type="http", auth="public", csrf=False)
def webhook(self):
    payload = request.httprequest.get_data()
    request.env["my.processor"].sudo().with_delay().process_webhook(payload)
    return Response("OK", status=200)  # ack immediately
```

The webhook responds in milliseconds; processing happens off the request cycle.

### Long-running cron decomposed
```python
def _cron_process_all(self):
    pending = self.search([("processed", "=", False)])
    for record in pending:
        record.with_delay().process_one()  # each is a queued job
```

## Without queue_job — basic decoupling

If you don't want the OCA dependency, you can still decouple via cron:

```python
def action_approve(self):
    super().action_approve()
    self.write({"needs_payroll_push": True})
    # And a cron picks up records with needs_payroll_push=True every minute
```

This works but is coarse and lacks retries. Use queue_job for anything serious.

## Common pitfalls

- Cron method without `@api.model` — fails because cron passes empty recordset.
- Cron with `interval_type="seconds"` set to a low value — Odoo polls cron with a minimum interval (`limit_time_real_cron` and the cron loop). Don't expect sub-second precision.
- Job that captures `self.env.user` in a closure but runs as `base.user_root` — confusing. Pass user IDs as args, not user objects.
- Long transactions in cron without `cr.commit()` — block other workers, hold locks, may hit `idle_in_transaction_session_timeout`.
- Forgetting `timeout=` on outbound HTTP calls in jobs — a hung external service blocks the worker.
- Mixing `@job` decorator with methods that have other decorators — order matters. `@job` typically goes outermost.
- Using `with_delay()` inside a transaction that might rollback — the job is enqueued before commit; the row exists when the tx rolls back. Use `with_delay()` after the work that might fail.
- Crons that send email per record without `force_send=False` — block the cron on SMTP.

## Decision tree

| Need | Choose |
|---|---|
| Recurring "every day at 3am" | `ir.cron` |
| User clicks button, wants response now, work continues in background | `queue_job` with `with_delay()` |
| Many small jobs, need parallelism | `queue_job` with channels |
| Critical with retries on transient failure | `queue_job` + `RetryableJobError` |
| Just decouple, no retries needed, no OCA deps | `ir.cron` polling a flag field |

## References

- [Odoo 17 — Scheduled actions](https://www.odoo.com/documentation/17.0/developer/reference/backend/data.html)
- [OCA queue_job](https://github.com/OCA/queue)
- [queue_job documentation](https://github.com/OCA/queue/tree/16.0/queue_job)
