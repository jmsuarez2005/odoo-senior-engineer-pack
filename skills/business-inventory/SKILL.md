---
name: business-inventory
description: Odoo 17 Inventory (stock) — warehouses, locations, routes, rules, picking types, lots/serials, putaway, removal strategies, quants, valuation. Use when configuring multi-warehouse, designing stock flows, customizing pickings, setting up barcodes, or troubleshooting stock moves.
---

# Business: Inventory (Odoo 17 — `stock`)

## What this app solves

Tracks where products are, how they move, and what they're worth:

- **Warehouse** — a physical site
- **Location** — a place inside (Stock, Output, Customers, Inventory adjustments)
- **Quant** — quantity of a product at a location
- **Stock Move** — a planned or done movement of qty from A to B
- **Picking** — a transfer document (delivery, receipt, internal) bundling moves
- **Operation Type / Picking Type** — what kind of transfer (Receipts, Deliveries, etc.)
- **Route** — a sequence of rules describing how a product flows
- **Lot / Serial** — traceability identifiers

It's the heart of any physical-product company. Connects with Sales (delivery), Purchase (receipt), MRP (component consumption), POS (real-time sales).

## Core models

| Model | Purpose |
|---|---|
| `stock.warehouse` | A site with locations + picking types |
| `stock.location` | Physical or virtual location |
| `stock.quant` | Quantity of product at location (current state) |
| `stock.move` | Planned/done movement (the action) |
| `stock.move.line` | Detail line on a move (lot, serial, location specifics) |
| `stock.picking` | Transfer (group of moves) |
| `stock.picking.type` | Operation type (Receipt, Delivery, Internal, MO) |
| `stock.rule` | "How do I supply X at location Y?" |
| `stock.route` | Sequence of stock rules |
| `stock.lot` | Lot/Serial number record |
| `stock.warehouse.orderpoint` | Reordering rule (min/max stock) |
| `stock.valuation.layer` | Inventory valuation history (FIFO/AVCO) |

## Location types (memorize)

| Type | Examples |
|---|---|
| `internal` | Stock, WH/Stock/Shelf-A, WH/Output |
| `customer` | "Customers" (virtual) — products go here on delivery |
| `supplier` | "Vendors" (virtual) — products come from here on receipt |
| `inventory` | "Inventory adjustment" (virtual) |
| `production` | MRP consumption / production virtual locations |
| `transit` | Inter-warehouse transfers |
| `view` | Tree-only nodes (no quants) |

A move from `internal` → `customer` is a delivery. From `supplier` → `internal` is a receipt. From `internal` → `inventory` is a count adjustment.

## Routes and rules — the engine

A **route** is a sequence of rules that describe "how to get product X to location Y". Standard routes:

- **Buy** — to fulfill a stock need, create a purchase order
- **Manufacture** — to fulfill, create a manufacturing order
- **Make to Order (MTO)** — never stock; trigger procurement on demand
- **Make to Stock** — produce/buy ahead, fulfill from stock
- **Drop-ship** — supplier ships directly to customer
- **3-step delivery** — pick → pack → ship (via internal locations)
- **3-step receipt** — receive → quality → stock

Routes can be set on:
- Product (per-product behavior)
- Warehouse (default for all products at this site)
- Operation type (default for transfers of this kind)

Customize by creating new `stock.rule` chains.

## Picking lifecycle

`draft` → `waiting` (waiting for another move) → `confirmed` → `assigned` (qty reserved) → `done` / `cancel`

When a sale order confirms, Odoo creates pickings in `confirmed` state. The reservation cron / `action_assign` checks if stock is available; if so, moves to `assigned`. The user marks lines done and validates → `done`.

## Configuration — what the consultant sets up

### Warehouses
- Code (2-letter), name, address
- Reception/delivery steps (1, 2, or 3 step)
- Default routes
- Resupply (from another warehouse?)

### Picking types
Each operation type has:
- Default source/destination location
- Default sequence (`WH/IN/00001`)
- Show fields (lots, packages, owner)
- Backorder policy

### Reordering rules (orderpoints)
Per product per location: when on-hand drops below min, create an order to bring back to max. Replenishment scheduler runs daily (cron) — it generates POs / MOs accordingly.

### Lots and serials
Per product, configure tracking:
- **None** — anonymous units
- **By Lot** — group of units share a lot number
- **By Unique Serial** — every unit has a unique S/N

Serial-tracked products require a serial entry on every move line. Lot-tracked products require a lot but multiple units share one lot.

### Removal strategies
Per category or per location: FIFO, FEFO (First Expired), LIFO, Closest. Drives which quant to consume first.

### Putaway rules
Per location + per product (or category): "always put bananas at WH/Stock/Cold-Storage". Drives where new arrivals get stored.

## Common customizations

### Custom warehouse flow (e.g. consignment)
Goods owned by supplier but stored at our warehouse. Solution: virtual "Consignment" location (sub of internal but with custom owner tracking).

```python
# Create a stock.location with usage='internal', custom 'is_consignment' flag
# Add owner_id at quant level (already supported)
# Custom report views to filter by owner
```

OCA `stock_consignment` provides a complete implementation.

### Multi-step delivery customization
Standard 3-step: Stock → Output → Shipping → Customer. To insert a "Quality" step:

```python
# Create a stock.location 'WH/Quality' (internal)
# Create a stock.rule: Stock → Quality (using QC picking type)
# Create another rule: Quality → Output
# Adjust the warehouse's delivery_route_id
```

### Custom picking type with custom logic
Inherit `stock.picking`:

```python
class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_done(self):
        # Custom validation before transferring
        for picking in self:
            if picking.picking_type_id.code == "outgoing":
                self._check_credit_limit(picking)
        return super().action_done()
```

### Custom valuation
Standard: Standard Cost / FIFO / AVCO per category. For weighted average across companies or LIFO (rare), build on `stock.valuation.layer`.

Most "we need a custom valuation" requests are reframable as: change the `cost_method` on the product category, or use OCA `stock_inventory_revaluation`.

### Barcode scanning customization
The Barcode app (Enterprise) has a configurable engine. To add a custom barcode action (e.g. "scan a custom QR to start a quality check"):

```python
class StockBarcodeOperation(models.Model):
    _inherit = "barcodes.barcode_events_mixin"

    def _on_barcode_scanned(self, barcode):
        if barcode.startswith("QC-"):
            return self._open_quality_check(barcode[3:])
        return super()._on_barcode_scanned(barcode)
```

### Auto-replenishment beyond orderpoints
For dynamic replenishment (forecasted demand, seasonality), build on top of orderpoints with a custom cron that adjusts `product_min_qty` / `product_max_qty`. Or use `stock_demand_forecast` from OCA.

## Reports & inventory analysis

Standard:
- Inventory Valuation report
- Stock at Date (historical "what did we have on date X")
- Forecast report (incoming + outgoing)
- ABC analysis (Enterprise)

Custom reports often live on `stock.move` or `stock.move.line` with read_group. Don't query `stock.quant` directly for historical analysis — quants are current state, not history. Use valuation layers.

## Integration touchpoints

| Pattern | Approach |
|---|---|
| **Sale → Stock** | Sale confirm creates pickings via `_action_launch_stock_rule` |
| **Stock → Account** | Move done creates `account.move` entries (via valuation) |
| **3PL warehouse** | Push picking to 3PL via API on `action_assign`; receive shipped status as webhook |
| **Receiving a shipment label from carrier** | `delivery` module (delivery.carrier with `_send_shipping`) |
| **External WMS** | Sync quants and pickings via webhook + `account.move`-style ledger |

## Common pitfalls

- Direct `stock.quant.write({"quantity": X})` to "fix" a count — bypasses move records, breaks audit. Use Inventory Adjustment.
- Forgetting `_check_company_auto = True` on a custom multi-company stock model — moves cross companies wrongly.
- Routes that loop (rule A → loc → rule B → loc → rule A) — infinite procurement. Test thoroughly.
- Manual `stock.move.create` without setting `picking_type_id` → orphaned move, hard to track.
- Reserving stock for very long-lived sale orders → reservation hoarding. Tune `auto_assign` and use `quant_priority`.
- Tracking serials on a high-volume product (consumables) — every line requires a serial; users hate it. Choose per-product based on actual traceability need.
- "Why are negative quants allowed?" — `stock.location.allow_negative` is False by default. If True, you can ship before receiving (planning), but valuation gets messy. Keep False unless you really mean it.

## OCA modules worth knowing

- `stock_picking_invoicing` — invoice from picking instead of order
- `stock_request` — internal stock requests (employee asks for stock)
- `stock_inventory_revaluation` — adjust inventory value
- `stock_demand_forecast` — better demand forecasting
- `stock_consignment` — consigned stock workflow
- `stock_dropshipping` — drop-ship enhancements
- `stock_picking_batch` — batch picking workflows

## References

- [Odoo Inventory documentation](https://www.odoo.com/documentation/17.0/applications/inventory_and_mrp/inventory.html)
- [OCA stock-logistics-warehouse](https://github.com/OCA/stock-logistics-warehouse)
- [OCA stock-logistics-workflow](https://github.com/OCA/stock-logistics-workflow)
