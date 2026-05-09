---
name: business-marketing
description: Odoo 17 Marketing — Email Marketing (mass_mailing), Marketing Automation (Enterprise), SMS Marketing, Events, Surveys, Social Marketing. Use when configuring marketing campaigns, drip flows, lead nurturing, A/B testing, or attribution tracking.
---

# Business: Marketing (Odoo 17)

## What this app suite solves

Outbound marketing + lead generation:
- **`mass_mailing`** — bulk email campaigns
- **`marketing_automation`** (Enterprise) — drip / nurture flows
- **`sms_marketing`** — bulk SMS
- **`event`** — events with registration, agenda, sponsors
- **`survey`** — surveys, quizzes, NPS
- **`social_marketing`** (Enterprise) — social media posts
- **`mass_mailing_sms`**, **`marketing_card`** — extras

## Core models

| Model | Purpose |
|---|---|
| `mailing.mailing` | An email/SMS campaign |
| `mailing.contact` | Subscriber |
| `mailing.list` | Mailing list |
| `mailing.trace` | Per-recipient send + engagement (opened, clicked, bounced) |
| `marketing.campaign` (Enterprise) | Automation flow |
| `marketing.activity` | Step in a campaign (send email, wait, condition) |
| `marketing.participant` | Recipient running through campaign |
| `event.event` | Event |
| `event.registration` | Attendee |
| `survey.survey` / `survey.question` / `survey.user_input` | Surveys |
| `utm.campaign` / `utm.source` / `utm.medium` | Attribution |

## Email marketing — `mass_mailing`

### Create a campaign
- Pick recipients: by mailing list, by domain on existing model (`res.partner`, `crm.lead`, etc.), or by contact filter
- Build email (drag-drop blocks)
- A/B test subject lines (variants)
- Schedule send

### Tracking
Each send creates `mailing.trace` records:
- `sent` (out the door)
- `opened` (pixel triggered)
- `clicked` (UTM-tagged link clicked)
- `bounced` (hard / soft)
- `unsubscribed`

### Bounces and opt-out
- Soft bounce: temporary, retry
- Hard bounce: blacklist email
- Unsubscribe: adds to `mail.blacklist`

### List management
`mailing.contact` is a separate model from `res.partner` (a marketing-only audience model). Connect via custom logic if needed.

## Marketing Automation (Enterprise)

Drag-drop flow builder:
- Trigger (record creation, field change, anniversary, manual)
- Activities (send email, send SMS, server action, send to expert, …)
- Conditions (split branches based on field, engagement)
- Wait (X days)

### Common flows
- **Welcome series**: trigger on partner creation → wait 1 day → email "welcome" → wait 3 days → email "tips" → wait 1 week → email "case studies"
- **Abandoned cart**: trigger on draft sale order > 24h → email "did you forget?" → if not opened in 2 days → email with discount
- **Customer reactivation**: trigger on customer with no order in 90 days → email re-engagement
- **Lead nurture by score**: branch on lead score; high-value leads get sales-rep notification, low-value get nurture sequence

### Custom triggers
Beyond standard, build a server action that creates `marketing.participant`:

```python
def _trigger_custom_campaign(self):
    campaign = self.env.ref("my_module.campaign_anniversary")
    for partner in self:
        if partner.create_date.date() == fields.Date.today() - timedelta(days=365):
            self.env["marketing.participant"].create({
                "campaign_id": campaign.id,
                "res_id": partner.id,
            })
```

## Events

`event.event` with registrations, ticket types, sponsors, sessions:
- Online or in-person
- Free or paid (links to `event_sale`)
- Registration via website (`website_event`) or backend
- Email confirmations, reminders
- Badges, attendance tracking

Custom: integrate with Zoom/Teams, custom registration fields, partner-only events.

## Surveys

Use cases:
- NPS surveys (post-sale, post-helpdesk)
- Quizzes (training)
- Job applicant questionnaires (hr_recruitment_survey)
- Customer feedback embedded on website pages

Each `survey.survey` has questions, scoring, and `survey.user_input` records (per response). Computed `quizz_passed` for pass/fail flows.

## Attribution (UTM)

Every mass mailing tags links with `?utm_source=&utm_medium=&utm_campaign=`. When a clicker arrives at the website and converts (creates a `crm.lead` or `sale.order`), the UTM is captured (via `utm.mixin`), enabling source-tracked reporting.

## Customizations

### Custom segmentation
"Send to all partners who bought product X but never product Y":

```python
def get_segment_partners(self):
    bought_x = self.env["sale.order"].search([
        ("state", "in", ("sale", "done")),
        ("order_line.product_id", "=", X),
    ]).mapped("partner_id")
    bought_y = self.env["sale.order"].search([
        ("state", "in", ("sale", "done")),
        ("order_line.product_id", "=", Y),
    ]).mapped("partner_id")
    return bought_x - bought_y
```

Use this in a custom mailing's recipient filter or pre-create `mailing.contact` records.

### Tracking opens/clicks beyond standard
Standard tracks open + click. For "watched the video for X seconds" or app events:

```python
@http.route("/track/event", type="http", auth="public", csrf=False, methods=["POST"])
def track_event(self, **post):
    request.env["mailing.trace"].sudo().write_event(...)
    return Response("OK")
```

### Custom A/B test logic
Standard has subject A/B. For body variants, more arms, or content-based winner picking, build a `mailing.test.variant` model.

### Lead scoring updates from engagement
"User opened email + clicked + visited pricing page → +20 lead score":

```python
class MailingTrace(models.Model):
    _inherit = "mailing.trace"

    def _set_clicked(self):
        super()._set_clicked()
        for trace in self:
            lead = self.env["crm.lead"].search([
                ("partner_id", "=", trace.res_id) if trace.model == "res.partner" else ("id", "=", trace.res_id),
            ], limit=1)
            if lead:
                lead.custom_score += 5
```

## Common pitfalls

- Sending without warming up domain → ESPs block all traffic. Use `mass_mailing` with rate limits, gradually scale up.
- No SPF/DKIM/DMARC → emails go to spam. Configure DNS before any campaign.
- Mailing list with stale contacts → high bounce rate damages reputation. Clean lists regularly.
- Forgetting unsubscribe link → CAN-SPAM / GDPR violation.
- Marketing automation with infinite loops → check for cycles in flow builder.
- UTM not propagated through redirects → attribution lost.
- Triggering campaigns from `marketing.participant.create` without rate limiting → API blast.

## OCA / community alternatives

- `mass_mailing_segment_*` — better segmentation
- `partner_event_marketing` — link partners to events
- `marketing_card_*` — gift card campaigns
- For drip flows without Enterprise, build with `ir.cron` + `mail.template` + state field on partner/lead.

## References

- [Odoo Email Marketing documentation](https://www.odoo.com/documentation/17.0/applications/marketing/email_marketing.html)
- [Odoo Marketing Automation (Enterprise)](https://www.odoo.com/documentation/17.0/applications/marketing/marketing_automation.html)
- [OCA marketing](https://github.com/OCA/marketing)
