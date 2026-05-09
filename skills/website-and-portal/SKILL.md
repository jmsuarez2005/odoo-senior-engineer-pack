---
name: website-and-portal
description: Build Odoo 17 public-facing pages — Website builder, controllers with auth=public, customer Portal pages, snippets, theme inheritance, and SEO. Use when adding public web pages, customer self-service portal, embedded forms, blog/landing/event pages, or public document access via portal.mixin.
---

# Website & Portal (Odoo 17)

## When to use this skill

Anything user-facing on the public web or customer portal. New landing page, public form, customer self-service area for orders/invoices, blog post type, event registration, embedded snippet, theme tweak.

## Two layers

| Layer | Module | Audience |
|---|---|---|
| **Website** | `website` | Public visitors (no login) |
| **Portal** | `portal` | Logged-in customers (limited backend access) |

A typical setup uses both: website for marketing/landing, portal for "view your invoices" / "my quotations".

## Website controllers (public pages)

```python
# controllers/main.py
from odoo import http
from odoo.http import request


class MyWebsite(http.Controller):

    @http.route("/about", type="http", auth="public", website=True)
    def about_page(self, **kwargs):
        return request.render("my_module.about_page", {
            "team_count": request.env["hr.employee"].sudo().search_count([]),
        })

    @http.route("/contact", type="http", auth="public", website=True, methods=["POST"], csrf=True)
    def contact_submit(self, **post):
        if not post.get("email") or "@" not in post.get("email", ""):
            return request.render("my_module.contact_error")
        # Public users can't write CRM leads — sudo with validated input
        request.env["crm.lead"].sudo().create({
            "name": f"Web inquiry: {post.get('name', '')}",
            "contact_name": post.get("name"),
            "email_from": post.get("email"),
            "description": post.get("message", ""),
        })
        return request.render("my_module.contact_thanks")
```

`website=True` enables:
- Multi-website routing (the right website's content is loaded)
- Multilang URL prefixing (`/es/about`, `/fr/about`)
- Page editor integration (Edit button works)

## Website templates

```xml
<template id="about_page" name="About Us">
    <t t-call="website.layout">
        <div class="container">
            <h1>About</h1>
            <p>We have <span t-out="team_count"/> team members.</p>
        </div>
    </t>
</template>
```

`website.layout` is the standard wrapper (header, footer, navbar). Use it for consistency.

## Adding a menu item

```xml
<record id="menu_about" model="website.menu">
    <field name="name">About</field>
    <field name="url">/about</field>
    <field name="parent_id" ref="website.main_menu"/>
    <field name="sequence">50</field>
</record>
```

## Snippets (drag-drop blocks)

A snippet is a reusable HTML block users can drop on any page via the editor.

```xml
<template id="s_my_block" name="My Block">
    <section class="s_my_block pt32 pb32" data-name="My Block">
        <div class="container">
            <h2>Headline</h2>
            <p>Body copy.</p>
        </div>
    </section>
</template>

<!-- Register in the snippet menu -->
<template id="s_my_block_options" name="My Block Options" inherit_id="website.snippets">
    <xpath expr="//div[@id='snippet_content']" position="inside">
        <t t-snippet="my_module.s_my_block"
           t-thumbnail="/my_module/static/description/s_my_block.svg"/>
    </xpath>
</template>
```

The visitor edits the page, drops the snippet, and any text/image inside is editable inline.

## Customer Portal

Portal pages let logged-in customers view their records (invoices, quotations, tickets) without backend UI.

### Make a model portal-accessible

```python
class HrOvertime(models.Model):
    _inherit = ["hr.overtime", "portal.mixin"]

    def _compute_access_url(self):
        super()._compute_access_url()
        for record in self:
            record.access_url = f"/my/overtime/{record.id}"

    def _get_portal_return_action(self):
        return self.env.ref("hr_overtime.action_hr_overtime")
```

`portal.mixin` adds:
- `access_token` — secure unique token
- `access_url` — URL for the customer
- `access_warning` — optional warning shown in the portal

### Portal controller

```python
from odoo.addons.portal.controllers.portal import CustomerPortal


class OvertimePortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "overtime_count" in counters:
            values["overtime_count"] = request.env["hr.overtime"].search_count(
                [("employee_id.user_id", "=", request.env.user.id)]
            )
        return values

    @http.route(["/my/overtime"], type="http", auth="user", website=True)
    def portal_my_overtimes(self, **kw):
        records = request.env["hr.overtime"].search(
            [("employee_id.user_id", "=", request.env.user.id)]
        )
        return request.render("hr_overtime.portal_my_overtimes", {
            "overtimes": records,
            "page_name": "overtime",
        })

    @http.route(["/my/overtime/<int:overtime_id>"], type="http", auth="public", website=True)
    def portal_overtime_detail(self, overtime_id, access_token=None, **kw):
        try:
            overtime_sudo = self._document_check_access(
                "hr.overtime", overtime_id, access_token=access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my")
        return request.render("hr_overtime.portal_overtime_detail", {
            "overtime": overtime_sudo,
            "page_name": "overtime",
        })
```

`_document_check_access` validates either logged-in user permissions OR an access token (for emailed links to non-portal customers).

### Portal counters on the home

The "My Account" portal page shows tiles for each portal-accessible record type. Add yours by overriding `_prepare_home_portal_values` (above) and adding to the home template:

```xml
<template id="portal_my_home_overtime" inherit_id="portal.portal_my_home">
    <xpath expr="//div[hasclass('o_portal_docs')]" position="inside">
        <t t-call="portal.portal_docs_entry">
            <t t-set="title">Overtime</t>
            <t t-set="url" t-value="'/my/overtime'"/>
            <t t-set="placeholder_count" t-value="'overtime_count'"/>
        </t>
    </xpath>
</template>
```

## Theme inheritance

Themes are modules that extend `website` with templates, snippets, CSS. To customize a theme:

```xml
<template id="my_theme_layout" inherit_id="theme_default.layout">
    <xpath expr="//header" position="attributes">
        <attribute name="class">my-custom-header</attribute>
    </xpath>
</template>
```

CSS via SCSS in `static/src/scss/`, asset bundle `web.assets_frontend`:

```python
"assets": {
    "web.assets_frontend": [
        "my_module/static/src/scss/website.scss",
    ],
},
```

## Multi-website

Multi-website lets one Odoo serve different brands/domains. Models that should be per-website use `website_id`:

```python
class ProductTemplate(models.Model):
    _inherit = "product.template"
    # website_id already exists on this model
```

Records with `website_id = NULL` are visible on all websites; with a specific ID, only on that one. Record rules handle the filtering.

## SEO

```xml
<template id="my_page">
    <t t-call="website.layout">
        <t t-set="head"><title>My Page Title</title>
            <meta name="description" content="..."/>
        </t>
        <!-- body -->
    </t>
</template>
```

Or via the page record:
```xml
<record id="page_about" model="website.page">
    <field name="name">About</field>
    <field name="website_meta_title">About — My Company</field>
    <field name="website_meta_description">...</field>
    <field name="is_published" eval="True"/>
</record>
```

`website_meta_*` fields are translatable and editable from the page settings.

## Forms with `csrf=True`

Browser-driven POSTs need CSRF protection:

```xml
<form action="/contact" method="post">
    <input type="hidden" name="csrf_token" t-att-value="request.csrf_token()"/>
    <input name="name" required="required"/>
    <input name="email" type="email" required="required"/>
    <textarea name="message"/>
    <button type="submit">Send</button>
</form>
```

`csrf=True` (the default) on `@http.route` rejects POSTs without the token.

## Common pitfalls

- `auth="public"` with no input validation → spam, abuse, security holes.
- Forgetting `csrf=True` on browser forms → opens CSRF vulnerability OR forgets the token in HTML and gets 400 on submit.
- Public controllers writing to backend models without `sudo()` → AccessError on every request.
- Writing without validation after `sudo()` → privilege escalation.
- Mixing `auth="user"` and a "public-but-shareable" link → use `auth="public"` + token validation via `_document_check_access`.
- Adding a website page without `website=True` on the route → multi-lang prefixing breaks, page editor doesn't work.
- Portal pages without `pager` for long lists → slow loads. Use `portal_pager`.
- Templates with `t-raw` of user input → XSS. Use `t-out` (HTML-escaped) or `t-field` with sanitize.
- Forms missing `required` server-side check (only client-side `required` HTML attribute) → bypassed by anyone with curl.

## References

- [Odoo 17 — Website](https://www.odoo.com/documentation/17.0/applications/websites/website.html)
- [Odoo 17 — Building blocks (snippets)](https://www.odoo.com/documentation/17.0/developer/howtos/website_themes/building_blocks.html)
- [Odoo 17 — Portal documentation](https://www.odoo.com/documentation/17.0/applications/general/users/portal.html)
- [Odoo 17 — http controllers](https://www.odoo.com/documentation/17.0/developer/reference/backend/http.html)
