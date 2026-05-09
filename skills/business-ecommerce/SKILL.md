---
name: business-ecommerce
description: Odoo 17 eCommerce (website_sale) — product catalog, cart, checkout, payment, B2B vs B2C, abandoned cart, multi-website, themes. Use when configuring or customizing the webshop, product variants display, checkout flow, or integrating with marketplaces.
---

# Business: eCommerce (Odoo 17 — `website_sale`)

## What this app solves

Public-facing webshop:
- Product catalog with categories, variants, attributes
- Cart and checkout
- Payment provider integration
- Customer accounts (portal)
- Abandoned cart recovery
- B2B (price ex tax, account approval) vs B2C (price inc tax, instant)
- Multi-website (multiple brands on one Odoo)

## Core models

| Model | Purpose |
|---|---|
| `product.template` / `product.product` | Catalog entries (existing models, extended for web) |
| `product.public.category` | Web-only category tree |
| `product.attribute` / `product.attribute.value` | Variant attributes (Color, Size) |
| `sale.order` | Cart = SO in `draft` state with `website_id` |
| `website` | The website definition (URL, default lang, currency, pricelist) |
| `payment.provider` / `payment.transaction` | Payment integration |

## Configuration

### Website
- Website URL, default language, default currency
- Default pricelist
- Tax computation (`tax_included` or excluded for display)
- Salesperson, sales team for orders

### Catalog
On `product.template`:
- `is_published` (visible on website)
- `website_sequence` (display order)
- `public_categ_ids` (web categories)
- `website_description` (rich-text page content)
- `website_url` (alias)

### Variants
- Define `product.attribute` (Color, Size)
- Add `product.attribute.value` per attribute
- On product template, list which attributes apply
- Each combination = a `product.product` variant
- Hide attributes per variant via `product.attribute.exclusion`

### Pricelists
- Public pricelist (anonymous users see this)
- B2B pricelists assigned per portal user
- Pricelist selector on website (currency / region)

### Payment providers
- Standard ships Stripe, PayPal, Adyen, Paystack, Razorpay, Authorize.net, etc.
- Each is a `payment.provider` record with credentials (test + production)
- Can enable per website + per pricelist (e.g. PayPal only for €)

### Delivery
- `delivery.carrier` records: rate per zone/weight, free above threshold, fixed
- Real-time integration with FedEx, UPS, USPS, DHL (Enterprise)

## Common customizations

### Custom checkout step
Standard checkout: Address → Shipping → Payment → Confirm. To insert a step (e.g. "agree to NDA"):

```python
class WebsiteSale(WebsiteSaleController):

    @http.route()
    def checkout(self, **post):
        order = request.website.sale_get_order()
        # If we haven't agreed yet, redirect to NDA page
        if order and not order.nda_accepted:
            return request.redirect("/shop/nda")
        return super().checkout(**post)
```

```python
@http.route(["/shop/nda"], type="http", auth="public", website=True)
def nda_page(self, **post):
    order = request.website.sale_get_order()
    if request.httprequest.method == "POST":
        order.nda_accepted = True
        return request.redirect("/shop/checkout")
    return request.render("my_module.nda_page", {"order": order})
```

### Custom product page block
Snippets and `website_description` cover most. For dynamic content (live stock count, related products by ML):

```xml
<template id="product_extra" inherit_id="website_sale.product">
    <xpath expr="//div[hasclass('o_wsale_product_main')]" position="inside">
        <div t-if="product.qty_available < 10" class="alert alert-warning">
            Only <t t-out="int(product.qty_available)"/> left!
        </div>
    </xpath>
</template>
```

### Restricted catalog (B2B login required)
Standard: `Public` users see all `is_published` products. To hide for non-logged-in:

```python
class ProductTemplate(models.Model):
    _inherit = "product.template"
    require_login = fields.Boolean()

    @api.model
    def _search(self, args, ...):
        # If user is public and product requires login, exclude
        if request.env.user.has_group("base.group_public"):
            args = [("require_login", "=", False)] + args
        return super()._search(args, ...)
```

Or simpler: use multi-website + record rules.

### Abandoned cart recovery
Standard: cron sends recovery email after configurable hours. Configure on website:
- `cart_abandoned_delay` — hours after which a draft cart is "abandoned"
- Mail template

To customize email content / timing tiers:
```python
@api.model
def _send_abandoned_cart_email(self):
    delays = [(2, "soft"), (24, "medium"), (72, "final")]
    for hours, level in delays:
        cutoff = fields.Datetime.now() - timedelta(hours=hours)
        carts = self.search([
            ("state", "=", "draft"),
            ("recovery_level", "=", level - 1 if level != "soft" else False),
            ("write_date", "<=", cutoff),
        ])
        for cart in carts:
            template = self.env.ref(f"my_module.cart_recovery_{level}")
            template.send_mail(cart.id)
            cart.recovery_level = level
```

### Custom payment flow
Build a new payment provider:

```python
class PaymentProvider(models.Model):
    _inherit = "payment.provider"
    code = fields.Selection(selection_add=[("mybank", "MyBank")], ondelete={"mybank": "set default"})

class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _send_payment_request(self):
        if self.provider_id.code != "mybank":
            return super()._send_payment_request()
        # call MyBank API, update self.state and self.provider_reference
```

Most often, **don't** build a payment provider. Use Stripe / Adyen which already integrate.

## Multi-website

One Odoo, multiple websites = multiple brands. Each `website` has:
- Own URL (or subpath)
- Own theme
- Own pricelist
- Own products (via `website_id` on product.template, or shared)
- Own languages

Record rules filter product / blog / page by `website_id`. Add `website_id` to your custom models if they should be per-site.

## Reports

Standard:
- eCommerce dashboard (revenue, top products, conversion)
- Abandoned cart analysis (Enterprise)

Custom: "Conversion funnel by traffic source" — join `sale.order` with `utm.*` fields.

## Integration touchpoints

| Pattern | Approach |
|---|---|
| **Stripe / PayPal** | Standard `payment_stripe`, `payment_paypal` |
| **Marketplace (Amazon, eBay, Mercado Libre)** | OCA `connector_*` or third-party connectors |
| **Shipping (FedEx, UPS, DHL)** | Standard `delivery_fedex`, `delivery_ups` |
| **Email marketing** | `mass_mailing`, sync customers as recipients |
| **Tax calculation (Avalara, TaxJar)** | OCA `account_avatax` etc. |
| **Inventory sync with marketplaces** | Cron pushes `qty_available` to marketplace API |
| **Reviews / ratings** | `website_sale_comparison`, custom `product.rating` model |

## Common pitfalls

- B2B store with prices VAT-inclusive (or vice versa) — costly tax mistakes. Check `tax_included` on website.
- Variants displayed in catalog without filters — 100 products × 5 colors × 5 sizes = 2500 listing items.
- Public pricelist accidentally shows internal cost — not just price. Always test as anonymous user.
- Checkout that requires login — kills B2C conversion. Allow guest checkout.
- Custom payment with no idempotency check — duplicate charges from retries.
- Heavy theme with un-bundled assets — slow page load. Use `web.assets_frontend` properly.
- Abandoned cart delay too aggressive (1 hour) — annoys customers, low convert.
- Checkout flow that doesn't handle out-of-stock during payment — overselling.

## OCA modules worth knowing

- `website_sale_*` (many) — extra checkout / catalog features
- `website_sale_b2b` — B2B-friendly defaults
- `website_sale_product_brand` — brand pages
- `website_sale_stock_provisioning_date` — show "ships on" date
- `website_sale_secondary_unit` — sell in alternate UoMs
- `connector_*` — marketplace connectors

## References

- [Odoo eCommerce documentation](https://www.odoo.com/documentation/17.0/applications/websites/ecommerce.html)
- [Odoo Payment providers](https://www.odoo.com/documentation/17.0/applications/finance/payment_providers.html)
- [OCA e-commerce](https://github.com/OCA/e-commerce)
