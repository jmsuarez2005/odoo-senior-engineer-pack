---
name: web-services-api
description: Build and consume Odoo 17 web services — XML-RPC, JSON-RPC, http.route controllers, REST patterns, webhooks, authentication. Use when integrating Odoo with external systems, exposing endpoints, or scripting Odoo from outside.
---

# Web Services & APIs (Odoo 17)

## When to use this skill

You're integrating Odoo with another system. Either Odoo is the server (you expose endpoints / controllers) or the client (you call other systems). Or you're building webhooks, REST APIs, or scripting Odoo from a CI pipeline.

## Two transport options out of the box

### XML-RPC

Simple, slow, language-agnostic. The classic Odoo external API.

```python
import xmlrpc.client

URL = "https://my.odoo.com"
DB = "my_db"
USERNAME = "admin@example.com"
API_KEY = "xxx"  # generate via Settings > Users > API Keys, NOT password

# Authenticate
common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
uid = common.authenticate(DB, USERNAME, API_KEY, {})

# Call methods
models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")
partner_ids = models.execute_kw(
    DB, uid, API_KEY,
    "res.partner", "search",
    [[["is_company", "=", True]]],
    {"limit": 10},
)
partners = models.execute_kw(
    DB, uid, API_KEY,
    "res.partner", "read",
    [partner_ids, ["name", "email", "phone"]],
)
```

### JSON-RPC

Same surface, JSON over HTTP. The transport the Odoo web client itself uses.

```python
import requests

session = requests.Session()
# /web/session/authenticate → cookie-based session
session.post(f"{URL}/web/session/authenticate", json={
    "params": {"db": DB, "login": USERNAME, "password": API_KEY},
})

# Call any model method
r = session.post(f"{URL}/web/dataset/call_kw", json={
    "params": {
        "model": "res.partner",
        "method": "search_read",
        "args": [],
        "kwargs": {
            "domain": [["is_company", "=", True]],
            "fields": ["name", "email"],
            "limit": 10,
        },
    },
}).json()
print(r["result"])
```

JSON-RPC is preferred for richer payloads and modern integrations.

## API keys, not passwords

In v17, password-based RPC auth is **disabled by default** in the standard config. Users generate API keys from Settings > Users > Account Security > API Keys. Each key has a name and is shown once.

In code, treat keys like passwords (env vars, secrets manager, never committed).

## Custom HTTP controllers

Define your own endpoints with `@http.route`.

```python
# controllers/main.py
import json
from odoo import http
from odoo.http import request, Response


class HrOvertimeController(http.Controller):

    @http.route("/api/overtime", type="json", auth="user", methods=["POST"])
    def submit_overtime(self, employee_id, hours, date, justification=None):
        """Submit a new overtime request as JSON-RPC."""
        overtime = request.env["hr.overtime"].create({
            "employee_id": employee_id,
            "hours": hours,
            "date": date,
            "justification": justification,
            "state": "submitted",
        })
        return {"id": overtime.id, "name": overtime.name}

    @http.route("/api/overtime/<int:overtime_id>", type="http", auth="user", methods=["GET"])
    def get_overtime(self, overtime_id):
        """Plain HTTP GET that returns JSON."""
        overtime = request.env["hr.overtime"].browse(overtime_id).exists()
        if not overtime:
            return Response("Not found", status=404)
        # ACL check happens implicitly when reading
        data = overtime.read(["name", "state", "hours", "date"])[0]
        return Response(json.dumps(data), content_type="application/json", status=200)
```

### `@http.route` parameters

| Param | Purpose |
|---|---|
| `route` | URL pattern; supports `<int:id>`, `<string:name>`, etc. |
| `type` | `"json"` (JSON-RPC envelope) or `"http"` (raw HTTP) |
| `auth` | `"user"`, `"public"`, `"none"`, `"bearer"` |
| `methods` | List of HTTP verbs |
| `csrf` | `False` to skip CSRF token (for non-browser clients) |
| `cors` | CORS origin (string or `"*"`) |

### `type="json"` vs `type="http"`

- `type="json"` — Odoo wraps your return value in `{"jsonrpc": "2.0", "id": ..., "result": ...}`. Errors get standard JSON-RPC error envelopes. Used by the web client.
- `type="http"` — you handle the raw request and response. Use for REST APIs, file downloads, redirects.

### `auth="public"` — the trust posture

Anyone on the internet can call this. Treat all input as untrusted:

```python
@http.route("/public/contact", type="http", auth="public", methods=["POST"], csrf=True)
def contact_form(self, **post):
    # Validate
    name = post.get("name", "").strip()
    email = post.get("email", "").strip()
    if not name or not email or "@" not in email:
        return request.redirect("/contact?error=1")

    # Use sudo because public users have no write access to crm.lead.
    # Trust boundary: this is the public lead intake; we validated input above.
    request.env["crm.lead"].sudo().create({
        "name": f"Web inquiry: {name}",
        "contact_name": name,
        "email_from": email,
        "description": post.get("message", ""),
    })
    return request.redirect("/contact?ok=1")
```

## Webhook receiver pattern

```python
import hmac
import hashlib

class StripeWebhookController(http.Controller):

    @http.route("/webhook/stripe", type="http", auth="public", methods=["POST"], csrf=False)
    def stripe_webhook(self):
        signature = request.httprequest.headers.get("Stripe-Signature", "")
        body = request.httprequest.get_data()  # raw bytes — required for HMAC
        secret = request.env["ir.config_parameter"].sudo().get_param("stripe.webhook_secret")

        if not self._verify_signature(body, signature, secret):
            return Response("Invalid signature", status=401)

        event = json.loads(body)
        # Idempotency: skip if event_id already processed
        if request.env["payment.transaction"].sudo().search(
            [("provider_reference", "=", event["id"])], limit=1
        ):
            return Response("Already processed", status=200)

        # Dispatch
        method = f"_handle_{event['type'].replace('.', '_')}"
        if hasattr(self, method):
            getattr(self, method)(event)

        return Response("OK", status=200)

    def _verify_signature(self, body, signature, secret):
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature.split(",")[-1])
```

Key points:
- `csrf=False` for webhook endpoints (no browser involved).
- Use the **raw body** for HMAC, not parsed JSON.
- Implement idempotency — webhook deliveries can repeat.
- Return 200 ASAP; queue heavy work via `ir.cron` or a queue lib.

## Bearer auth (token-based REST)

```python
@http.route("/api/v1/orders", type="http", auth="bearer", methods=["GET"])
def list_orders(self):
    # request.env.user is set from the token automatically
    orders = request.env["sale.order"].search([], limit=50)
    return Response(
        json.dumps([{"id": o.id, "name": o.name, "amount_total": o.amount_total} for o in orders]),
        content_type="application/json",
    )
```

`auth="bearer"` validates `Authorization: Bearer <api_key>` against `res.users.api.keys`.

## Outbound HTTP from Odoo

```python
import requests

class HrOvertime(models.Model):
    _inherit = "hr.overtime"

    def action_send_to_payroll(self):
        for record in self:
            response = requests.post(
                self.env["ir.config_parameter"].sudo().get_param("payroll.api_url"),
                json={"employee_id": record.employee_id.id, "hours": record.hours},
                headers={"Authorization": f"Bearer {self._get_payroll_token()}"},
                timeout=10,  # ALWAYS set timeout
            )
            response.raise_for_status()
            record.payroll_ref = response.json()["ref"]
```

Always:
- Set `timeout` (5-30s typical)
- Catch `requests.RequestException` and decide retry vs fail
- Don't block long requests — queue with `ir.cron` or commit-and-resume

## Pagination for list endpoints

```python
@http.route("/api/v1/partners", type="http", auth="bearer", methods=["GET"])
def list_partners(self, page=1, page_size=50):
    page = int(page)
    page_size = min(int(page_size), 200)  # cap
    offset = (page - 1) * page_size
    domain = []
    total = request.env["res.partner"].search_count(domain)
    partners = request.env["res.partner"].search_read(
        domain, ["name", "email"], limit=page_size, offset=offset, order="id"
    )
    return Response(json.dumps({
        "results": partners,
        "total": total,
        "page": page,
        "page_size": page_size,
    }), content_type="application/json")
```

## Common pitfalls

- Forgetting `csrf=False` on a non-browser POST endpoint → 400 with cryptic error.
- Using `request.params` for raw bodies → for POST with JSON body, use `request.httprequest.get_data()`.
- Not setting `methods=` → endpoint accepts any verb; surprising security holes.
- `auth="public"` with `cr.execute` and no input validation → SQL injection or data leak.
- Using `password` instead of API key in v17 RPC → auth fails silently in some configs.
- Webhook handler that does heavy work synchronously → upstream times out and retries, creating duplicates.
- Building REST endpoints that mirror every model field → leaking internal fields. Whitelist what's exposed.
- Forgetting CORS for browser-side integrations → opaque errors. Set `cors="https://your.domain"`.

## References

- [Odoo 17 — Web services tutorial](https://www.odoo.com/documentation/17.0/developer/howtos/web_services.html)
- [Odoo 17 — Controllers (HTTP routing)](https://www.odoo.com/documentation/17.0/developer/reference/backend/http.html)
- [Odoo 17 — External API](https://www.odoo.com/documentation/17.0/developer/reference/external_api.html)
