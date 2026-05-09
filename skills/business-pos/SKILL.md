---
name: business-pos
description: Odoo 17 Point of Sale (point_of_sale) — POS sessions, orders, payments, restaurant features, kitchen printers, hardware proxy. Use when configuring retail/restaurant POS, customizing the POS UI (OWL-based), integrating payment terminals, or syncing offline-capable orders.
---

# Business: Point of Sale (Odoo 17 — `point_of_sale`)

## What this app solves

Front-of-house sales:
- POS sessions (open / close, with cash counts)
- Customer-facing screen, cashier UI
- Receipt printing, kitchen printing
- Cash management
- Discount / loyalty / coupons
- Restaurant: tables, orders, courses, splits
- Offline mode (cache + sync when reconnected)
- Payment terminal integration

## Core models

| Model | Purpose |
|---|---|
| `pos.config` | A POS terminal configuration |
| `pos.session` | One open session (typically one shift) |
| `pos.order` | A sale done at POS |
| `pos.order.line` | Line item |
| `pos.payment` | Payment on POS order |
| `pos.payment.method` | Payment method definition |
| `pos.category` | Category in the POS UI |
| `restaurant.table` / `restaurant.floor` | Tables (Restaurant features) |

## Configuration

### POS config (terminal)
- Picking type (warehouse + operation type for stock movements)
- Sales journal (where invoices/orders post)
- Pricelists allowed
- Customer required, employees, cash control
- Payment methods (cash, card, gift, …)
- Restaurant features (if applicable)
- Receipt header/footer

### Hardware
- Receipt printer (network IP or via IoT Box)
- Kitchen printers (per category route)
- Cash drawer (opens via printer)
- Customer display (second screen)
- Barcode scanner

### Payment terminals
- Adyen, Stripe, Worldline, Six (varies by region)
- Configure terminal serial / store ID per `pos.payment.method`

## Lifecycle

1. Manager opens session: `pos.session.action_pos_session_open`
2. Cashier sells: each `pos.order` is a finalized sale
3. Manager closes session: counts cash, validates, generates accounting entries

The session is the **batch** that posts to accounting. Per-order = pos.order.line + pos.payment; per-session = `account.move` summary.

## Customizations

### Custom POS UI button (OWL)
The POS UI is a single-page OWL app. Adding a custom button:

```js
/** @odoo-module **/
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";

patch(ProductScreen.prototype, {
    setup() {
        super.setup();
    },

    async onCustomButtonClick() {
        const order = this.pos.get_order();
        // do something
        order.add_orderline(...);
    },
});
```

```xml
<t t-inherit="point_of_sale.ProductScreen" t-inherit-mode="extension">
    <xpath expr="//div[@class='control-buttons']" position="inside">
        <button class="control-button" t-on-click="onCustomButtonClick">
            <i class="fa fa-star"/>
            My Action
        </button>
    </xpath>
</t>
```

### Custom field on POS order
Add a Python field on `pos.order` AND make it transmittable from frontend:

```python
class PosOrder(models.Model):
    _inherit = "pos.order"
    custom_note = fields.Char()

    @api.model
    def _order_fields(self, ui_order):
        fields_dict = super()._order_fields(ui_order)
        fields_dict["custom_note"] = ui_order.get("custom_note", "")
        return fields_dict
```

```js
// Order model in frontend
import { Order } from "@point_of_sale/app/store/models";
patch(Order.prototype, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
        this.custom_note = options.json?.custom_note || "";
    },
    export_as_JSON() {
        const json = super.export_as_JSON();
        json.custom_note = this.custom_note;
        return json;
    },
});
```

### Custom receipt (OWL template)
```xml
<t t-inherit="point_of_sale.OrderReceipt" t-inherit-mode="extension">
    <xpath expr="//div[@class='pos-receipt-amount']" position="after">
        <div class="pos-receipt-thanks">Thank you for shopping with us!</div>
    </xpath>
</t>
```

### Pre-paid / gift cards
Standard supports loyalty, gift cards via `loyalty` module. Customize redemption rules.

### Restaurant table layout
Drag-drop table layout via floor editor. Custom: programmatic table generation:

```python
floor = self.env.ref("my_module.floor_terrace")
for i in range(1, 10):
    self.env["restaurant.table"].create({
        "name": f"T-{i:02}", "floor_id": floor.id,
        "position_h": (i % 5) * 100, "position_v": (i // 5) * 100,
        "width": 80, "height": 80, "shape": "round",
        "seats": 4,
    })
```

### Offline mode
POS UI caches:
- Products + variants + stock
- Customers
- Pricelists
- Tax rules

When offline, orders queue locally. On reconnect, sync. **Do not** add custom logic that requires server roundtrip during checkout — breaks offline.

## Reports

Standard:
- POS daily report
- Orders by session
- Sales by product / category
- Cash control sheets

## Integration touchpoints

| Pattern | Approach |
|---|---|
| **Payment terminal** | Standard providers (Adyen, Stripe Terminal, Worldline) |
| **Loyalty programs** | `loyalty` module + custom rule types |
| **Kitchen printer** | Per-category print routing in POS config |
| **Self-order kiosk** | OCA `pos_self_order` or Enterprise self-order |
| **Online order pickup** | Bridge from `website_sale` orders to a POS pickup queue |
| **External inventory check** | Custom backend RPC during search-product |

## Common pitfalls

- Custom field added in Python without frontend serialization → field is empty on saved orders.
- POS UI customization that breaks the offline cache → users can't check out when WiFi drops.
- Tax computation discrepancy between POS UI (computed in JS) and backend (recomputed in Python on save) — round consistently.
- Stock movements happening at order creation rather than at session close — race conditions in busy stores.
- Receipt printer IP changing — POS won't print, no error message in UI. Add health-check.
- Discount approval bypassed by cashiers — use `pos.config` discount permissions per group.

## OCA modules worth knowing

- `pos_order_to_sale_order` — convert POS to standard SO
- `pos_payment_change` — change payment after close
- `pos_pricelist_by_customer` — auto-pick pricelist by customer
- `pos_loyalty_*` — extra loyalty features
- `pos_session_close_validation` — require manager to close

## References

- [Odoo POS documentation](https://www.odoo.com/documentation/17.0/applications/sales/point_of_sale.html)
- [Odoo IoT Box documentation](https://www.odoo.com/documentation/17.0/applications/general/iot.html)
- [OCA pos](https://github.com/OCA/pos)
