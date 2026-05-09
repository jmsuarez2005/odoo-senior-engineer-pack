---
name: qweb-reports
description: Build Odoo 17 QWeb PDF reports — paperformat, report actions, headers/footers, t-out vs t-esc, multi-page tables. Use when generating PDF invoices, certificates, statements, or any printable document.
---

# QWeb Reports (Odoo 17)

## When to use this skill

You need to produce a printable PDF: invoices, delivery slips, certificates, custom statements. Two reasons people get this wrong: missing the `t-out` vs `t-esc` distinction, and using `<table>` without page-break logic.

## The three pieces

1. **Report action** (`ir.actions.report`) — declares the report and links template + paperformat.
2. **Paperformat** (`report.paperformat`) — page size, margins, header/footer height.
3. **QWeb template** (`ir.ui.view` of type `qweb`) — the actual XML that renders to HTML, then to PDF.

## Report action

```xml
<record id="action_report_overtime" model="ir.actions.report">
    <field name="name">Overtime Slip</field>
    <field name="model">hr.overtime</field>
    <field name="report_type">qweb-pdf</field>          <!-- qweb-pdf | qweb-html | qweb-text -->
    <field name="report_name">hr_overtime.report_overtime_template</field>
    <field name="report_file">hr_overtime.report_overtime_template</field>
    <field name="binding_model_id" ref="model_hr_overtime"/>
    <field name="binding_type">report</field>
    <field name="paperformat_id" ref="hr_overtime.paperformat_overtime"/>
</record>
```

`binding_model_id` + `binding_type="report"` makes it appear in the Print menu of `hr.overtime` records.

## Paperformat

```xml
<record id="paperformat_overtime" model="report.paperformat">
    <field name="name">Overtime A4</field>
    <field name="default" eval="False"/>
    <field name="format">A4</field>
    <field name="orientation">Portrait</field>
    <field name="margin_top">40</field>
    <field name="margin_bottom">23</field>
    <field name="margin_left">7</field>
    <field name="margin_right">7</field>
    <field name="header_line" eval="False"/>
    <field name="header_spacing">35</field>
    <field name="dpi">90</field>
</record>
```

`margin_top` must be ≥ `header_spacing` or content collides with the header.

## The template

```xml
<template id="report_overtime_template">
    <t t-call="web.html_container">
        <t t-foreach="docs" t-as="o">
            <t t-call="web.external_layout">
                <div class="page">
                    <h2>Overtime Slip <span t-out="o.name"/></h2>

                    <div class="row mt-4">
                        <div class="col-6">
                            <strong>Employee:</strong>
                            <span t-field="o.employee_id"/>
                        </div>
                        <div class="col-6">
                            <strong>Date:</strong>
                            <span t-field="o.date" t-options='{"widget": "date"}'/>
                        </div>
                    </div>

                    <table class="table table-sm mt-4">
                        <thead>
                            <tr>
                                <th>Description</th>
                                <th class="text-end">Hours</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><span t-out="o.justification or 'Overtime work'"/></td>
                                <td class="text-end">
                                    <span t-out="o.hours" t-options='{"widget": "float", "precision": 2}'/>
                                </td>
                            </tr>
                        </tbody>
                    </table>

                    <p class="mt-4">
                        Approved on <span t-field="o.write_date" t-options='{"widget": "date"}'/>
                        by <span t-out="o.write_uid.name"/>.
                    </p>
                </div>
            </t>
        </t>
    </t>
</template>
```

`docs` is the recordset passed in (Odoo passes one record at a time when printing from a button, multiple when batch-printing).

## QWeb directives — the ones you'll actually use

| Directive | Purpose | Example |
|---|---|---|
| `t-out` | Output a value, HTML-safe | `<span t-out="record.name"/>` |
| `t-esc` | (deprecated alias for t-out, prefer t-out) | — |
| `t-field` | Output with field-aware widget | `<span t-field="o.amount" t-options='{"widget": "monetary", "display_currency": o.currency_id}'/>` |
| `t-foreach` / `t-as` | Loop | `<tr t-foreach="o.line_ids" t-as="line">...</tr>` |
| `t-if` / `t-elif` / `t-else` | Conditional | `<div t-if="o.state == 'approved'">Approved</div>` |
| `t-call` | Render another template | `<t t-call="web.external_layout">...</t>` |
| `t-set` / `t-value` | Local variable | `<t t-set="total" t-value="sum(o.line_ids.mapped('amount'))"/>` |
| `t-att-X` / `t-attf-X` | Dynamic attributes | `<div t-att-class="'success' if o.state == 'approved' else 'danger'"/>` |
| `t-raw` | Output raw HTML (DANGEROUS) | Avoid; use `t-out` with explicit HTML field |

### `t-out` vs `t-field`

- `t-out` outputs whatever expression you give it, escaping HTML. Use for arbitrary expressions.
- `t-field` is field-aware — uses the field's widget for formatting, knows about Many2one display, monetary precision, etc. Use for direct field rendering.

```xml
<!-- Both produce the same for a Char -->
<span t-out="o.name"/>
<span t-field="o.name"/>

<!-- t-field knows about currency formatting -->
<span t-field="o.amount" t-options='{"widget": "monetary", "display_currency": o.currency_id}'/>

<!-- t-out for computed expressions -->
<span t-out="sum(o.line_ids.mapped('amount'))"/>
```

## Headers, footers, and `web.external_layout`

`web.external_layout` is the standard wrapper that adds:
- Company logo + address in the header
- Page number footer
- Company info / phone in the footer

Use it as the outermost wrap inside `web.html_container`. It picks the layout based on `res.company.external_report_layout_id` (Standard, Boxed, Bold, Striped, Folder).

For a fully custom header/footer, declare them in the paperformat or override `web.external_layout`.

## Multi-page tables

Long tables need page-break-friendly rendering. Bootstrap's table classes already handle this in the wkhtmltopdf rendering Odoo uses. For very long tables, repeat the header on each page:

```xml
<table class="table">
    <thead>
        <tr>
            <th>...</th>
        </tr>
    </thead>
    <tbody>
        <tr t-foreach="o.line_ids" t-as="line">
            <td>...</td>
        </tr>
    </tbody>
</table>
```

`<thead>` is treated as a page header by wkhtmltopdf. Avoid wrapping rows in `<div>` — that breaks the table model.

## Internationalization in reports

Use `lang` parameter in the report action:

```xml
<field name="lang">{{ object.partner_id.lang }}</field>
```

(Yes, Jinja-like syntax in this specific field. Odoo evaluates it.)

In the template, all user-facing strings should be wrapped:
```xml
<th><t t-out="_('Description')"/></th>
```

## Programmatic generation

```python
report = self.env.ref("hr_overtime.action_report_overtime")
pdf_content, _ = report._render_qweb_pdf(report.report_name, res_ids=self.ids)
# pdf_content is bytes; attach to mail, store, etc.
```

## Common pitfalls

- Using `t-esc` on HTML fields — escapes the markup. Use `t-field` (which knows the field is HTML).
- Missing `web.html_container` wrapper — wkhtmltopdf renders without `<html>/<body>` and styles get lost.
- Hardcoding the company logo URL — it varies by company. Use `web.external_layout`.
- Margins too small for the header/footer — content overlaps. Match `margin_top` to header height.
- Forgetting `t-foreach` over `docs` — the report renders once with `docs` as a recordset of N, but if you don't loop, only one record appears.
- `report_name` and `report_file` must match the template's external ID (`module.template_id`). Mismatch = "QWeb report not found".
- Inline styles via `<style>` inside the template — wkhtmltopdf parses them, but Bootstrap classes are usually enough. Resort to inline CSS only when needed.
- Putting business logic in QWeb (like database writes) — templates are for rendering. Compute in the model, pass via `docs`.

## References

- [Odoo 17 — Reports](https://www.odoo.com/documentation/17.0/developer/reference/backend/reports.html)
- [Odoo 17 — QWeb](https://www.odoo.com/documentation/17.0/developer/reference/frontend/qweb.html)
