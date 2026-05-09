---
name: mixins-and-mail
description: Wire up Odoo 17 mixins — mail.thread, mail.activity.mixin, portal.mixin, image.mixin, utm.mixin, rating.mixin. Use when adding chatter, activities, portal access, image fields, or any standard mixin behavior.
---

# Mixins & Mail (Odoo 17)

## When to use this skill

You need to add chatter, scheduled activities, portal access, an avatar/image, rating, UTM tracking, or any other mixin-provided behavior. Don't reinvent — Odoo ships these mixins for a reason.

## `mail.thread` — chatter

The chatter is the chronological log + comments + email integration on a record.

```python
class HrOvertime(models.Model):
    _name = "hr.overtime"
    _inherit = ["mail.thread"]   # add to _inherit list

    name = fields.Char(tracking=True)               # tracking=True logs changes to chatter
    state = fields.Selection([...], tracking=True)
    employee_id = fields.Many2one("hr.employee", tracking=True)
```

Then in the form view:
```xml
<form>
    <sheet>...</sheet>
    <div class="oe_chatter">
        <field name="message_follower_ids"/>
        <field name="message_ids"/>
    </div>
</form>
```

### What you get for free
- `message_post(body=..., subject=..., subtype_xmlid=...)` to add a message programmatically
- Followers (people who get notified)
- Email gateway (replies-by-email update the record)
- Field-change tracking (with `tracking=True`)
- Subtype filtering (notes vs comments vs status changes)

### Posting a message in code
```python
self.message_post(
    body=_("Overtime approved by %s") % self.env.user.name,
    subtype_xmlid="mail.mt_comment",
)
```

### Subscribing followers
```python
self.message_subscribe(partner_ids=[self.employee_id.user_id.partner_id.id])
```

## `mail.activity.mixin` — scheduled activities

Activities are "things to do" attached to records (To-do, Call, Meeting, Email).

```python
class HrOvertime(models.Model):
    _inherit = ["mail.thread", "mail.activity.mixin"]
```

```xml
<div class="oe_chatter">
    <field name="message_follower_ids"/>
    <field name="activity_ids"/>
    <field name="message_ids"/>
</div>
```

### Scheduling an activity in code
```python
self.activity_schedule(
    "mail.mail_activity_data_todo",
    summary=_("Review overtime request"),
    user_id=self.env.user.id,
    date_deadline=fields.Date.today() + timedelta(days=2),
)
```

The first arg is the activity type's external ID. Common ones live in `mail`:
- `mail.mail_activity_data_todo`
- `mail.mail_activity_data_call`
- `mail.mail_activity_data_meeting`
- `mail.mail_activity_data_email`

You can define your own with `<record model="mail.activity.type">`.

## `portal.mixin` — public-facing record access

Lets a partner see a record via a tokenized URL without logging in (or via the Customer Portal if they have a portal user).

```python
class SaleOrder(models.Model):
    _inherit = ["sale.order", "portal.mixin"]

    def _get_portal_return_action(self):
        return self.env.ref("sale.action_quotations_with_onboarding")
```

You also wire up controller routes (`/my/orders/<int:order_id>?access_token=...`) and a portal template. See the `web-services-api` skill for controller patterns.

## `image.mixin` — image with auto-resized variants

Adds `image_1920`, `image_1024`, `image_512`, `image_256`, `image_128` fields. The mixin auto-resizes from the original `image_1920` upload.

```python
class HrEmployee(models.Model):
    _inherit = ["hr.employee", "image.mixin"]
```

In views you typically reference `image_1920` for upload, and the smaller variants for displays:
```xml
<field name="image_1920" widget="image" class="oe_avatar"
       options="{'preview_image': 'image_128'}"/>
```

## `utm.mixin` — campaign tracking

Adds `campaign_id`, `source_id`, `medium_id`. Useful for marketing-attribution chains.

```python
class CrmLead(models.Model):
    _inherit = ["crm.lead", "utm.mixin"]
```

## `rating.mixin` — 1-to-5 ratings tied to a record

```python
class HelpdeskTicket(models.Model):
    _inherit = ["helpdesk.ticket", "rating.mixin"]
```

You get `rating_ids`, `rating_avg`, plus methods for sending rating-request emails.

## Combining mixins

Order doesn't matter for mixins (they all extend independently), but conventionally:

```python
_inherit = [
    "mail.thread",
    "mail.activity.mixin",
    "portal.mixin",
    "image.mixin",
]
```

Or, if extending an existing model:

```python
_inherit = ["res.partner", "mail.thread", "image.mixin"]
```

(`res.partner` already has `mail.thread`, but listing it again is harmless — Odoo deduplicates.)

## Activity types — defining your own

```xml
<record id="mail_activity_overtime_review" model="mail.activity.type">
    <field name="name">Review Overtime</field>
    <field name="summary">Review and approve overtime request</field>
    <field name="res_model">hr.overtime</field>
    <field name="icon">fa-clock-o</field>
    <field name="delay_count">2</field>
    <field name="delay_unit">days</field>
    <field name="delay_from">previous_activity</field>
</record>
```

## Mail templates

```xml
<record id="email_template_overtime_approved" model="mail.template">
    <field name="name">Overtime: Approved</field>
    <field name="model_id" ref="model_hr_overtime"/>
    <field name="subject">Overtime approved</field>
    <field name="email_from">{{ object.company_id.email_formatted }}</field>
    <field name="email_to">{{ object.employee_id.work_email }}</field>
    <field name="body_html" type="html">
        <div>
            <p>Hello <t t-out="object.employee_id.name"/>,</p>
            <p>Your overtime request for
               <t t-out="object.hours"/> hours on
               <t t-out="format_date(object.date)"/> has been approved.</p>
        </div>
    </field>
    <field name="auto_delete" eval="True"/>
</record>
```

Send it:
```python
template = self.env.ref("hr_overtime.email_template_overtime_approved")
template.send_mail(self.id, force_send=True)
```

Use `force_send=True` only for low-volume / user-initiated sends. Mass sends should queue.

## Common pitfalls

- `tracking=True` on a non-stored computed field — silently does nothing.
- Forgetting the chatter `<div class="oe_chatter">` block — fields exist but nothing renders.
- Inheriting `mail.activity.mixin` without `mail.thread` — works but you lose the activity-related chatter integration.
- Using `subtype_xmlid="mail.mt_note"` for things customers should see — internal notes are NOT sent by email.
- Posting messages in `create()` before the record is fully constructed — leads to references to a half-built record. Post in a follow-up after `super().create()`.
- Sending mail templates with `force_send=True` in a loop — blocks the request. Queue instead.
- `image.mixin` on a model that already has its own image fields — collisions; remove the old fields first.

## Decision table

| You want… | Add this |
|---|---|
| Chatter with messages + log | `mail.thread` |
| Activities (To-do, Call, etc) | `mail.activity.mixin` |
| Avatar / picture | `image.mixin` |
| Customer portal page | `portal.mixin` + portal controller |
| Marketing attribution | `utm.mixin` |
| Rating widget | `rating.mixin` |

## References

- [Odoo 17 — Mixins](https://www.odoo.com/documentation/17.0/developer/reference/backend/mixins.html)
- [Odoo 17 — Discuss / mail](https://www.odoo.com/documentation/17.0/applications/productivity/discuss.html)
