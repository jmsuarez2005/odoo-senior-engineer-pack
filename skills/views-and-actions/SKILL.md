---
name: views-and-actions
description: Build Odoo 17 views (form, list, kanban, search, graph, pivot, calendar, gantt, activity), window/server actions, and menus. Use whenever creating XML views, inheriting views with xpath, defining ir.actions.act_window, or wiring menus.
---

# Views & Actions (Odoo 17)

## When to use this skill

Anything in `views/*.xml`. Form, list (note: `<list>` not `<tree>` in v17), kanban, search, graph, pivot, calendar, gantt, activity views. Window actions, server actions, menu items, view inheritance.

## v17 specific: `<list>` replaces `<tree>`

Odoo 17 renamed the `tree` view to `list`. Old XML still loads (compatibility shim) but new code MUST use `<list>`. The `view_mode` on actions is now `"list,form"` (not `"tree,form"`).

```xml
<record id="view_hr_overtime_list" model="ir.ui.view">
    <field name="name">hr.overtime.list</field>
    <field name="model">hr.overtime</field>
    <field name="arch" type="xml">
        <list string="Overtime Requests" decoration-success="state == 'approved'"
              decoration-muted="state == 'refused'" sample="1">
            <field name="name"/>
            <field name="employee_id"/>
            <field name="date"/>
            <field name="hours" sum="Total Hours"/>
            <field name="state" widget="badge"
                   decoration-info="state == 'draft'"
                   decoration-success="state == 'approved'"/>
            <field name="company_id" optional="show" groups="base.group_multi_company"/>
        </list>
    </field>
</record>
```

## Form view skeleton

```xml
<record id="view_hr_overtime_form" model="ir.ui.view">
    <field name="name">hr.overtime.form</field>
    <field name="model">hr.overtime</field>
    <field name="arch" type="xml">
        <form string="Overtime Request">
            <header>
                <button name="action_submit" string="Submit" type="object"
                        class="oe_highlight" invisible="state != 'draft'"/>
                <button name="action_approve" string="Approve" type="object"
                        class="oe_highlight" invisible="state != 'submitted'"
                        groups="hr_overtime.group_overtime_manager"/>
                <button name="action_refuse" string="Refuse" type="object"
                        invisible="state != 'submitted'"
                        groups="hr_overtime.group_overtime_manager"/>
                <field name="state" widget="statusbar" statusbar_visible="draft,submitted,approved"/>
            </header>
            <sheet>
                <div class="oe_button_box" name="button_box">
                    <button class="oe_stat_button" type="object" name="action_view_attachments"
                            icon="fa-paperclip">
                        <field name="attachment_count" widget="statinfo" string="Attachments"/>
                    </button>
                </div>
                <widget name="web_ribbon" title="Approved" bg_color="text-bg-success"
                        invisible="state != 'approved'"/>
                <div class="oe_title">
                    <h1><field name="name" readonly="state != 'draft'"/></h1>
                </div>
                <group>
                    <group>
                        <field name="employee_id" readonly="state != 'draft'"/>
                        <field name="date" readonly="state != 'draft'"/>
                    </group>
                    <group>
                        <field name="hours" readonly="state != 'draft'"/>
                        <field name="company_id" groups="base.group_multi_company"/>
                    </group>
                </group>
                <notebook>
                    <page string="Justification" name="justification">
                        <field name="justification" placeholder="Reason for overtime..."/>
                    </page>
                </notebook>
            </sheet>
            <div class="oe_chatter">
                <field name="message_follower_ids"/>
                <field name="activity_ids"/>
                <field name="message_ids"/>
            </div>
        </form>
    </field>
</record>
```

### v17 attribute changes

In v17, `attrs="{...}"` and `states="..."` are **deprecated**. Use direct attributes:

```xml
<!-- OLD (v16 and earlier) -->
<field name="hours" attrs="{'readonly': [('state', '!=', 'draft')]}"/>

<!-- NEW (v17) -->
<field name="hours" readonly="state != 'draft'"/>
```

Conditions are Python-like expressions evaluated against the record. `invisible`, `readonly`, `required`, `column_invisible` (list-only) all use this syntax now.

## Search view

```xml
<record id="view_hr_overtime_search" model="ir.ui.view">
    <field name="name">hr.overtime.search</field>
    <field name="model">hr.overtime</field>
    <field name="arch" type="xml">
        <search>
            <field name="name"/>
            <field name="employee_id"/>
            <filter name="my_overtime" string="My Overtime"
                    domain="[('employee_id.user_id', '=', uid)]"/>
            <filter name="this_month" string="This Month"
                    domain="[('date', '>=', (context_today() + relativedelta(day=1)).strftime('%Y-%m-%d'))]"/>
            <separator/>
            <filter name="draft" string="Draft" domain="[('state', '=', 'draft')]"/>
            <filter name="approved" string="Approved" domain="[('state', '=', 'approved')]"/>
            <group string="Group By">
                <filter name="group_employee" string="Employee" context="{'group_by': 'employee_id'}"/>
                <filter name="group_state" string="State" context="{'group_by': 'state'}"/>
                <filter name="group_date" string="Month" context="{'group_by': 'date:month'}"/>
            </group>
        </search>
    </field>
</record>
```

## Kanban (essentials)

```xml
<record id="view_hr_overtime_kanban" model="ir.ui.view">
    <field name="name">hr.overtime.kanban</field>
    <field name="model">hr.overtime</field>
    <field name="arch" type="xml">
        <kanban default_group_by="state" sample="1">
            <field name="state"/>
            <field name="employee_id"/>
            <templates>
                <t t-name="kanban-box">
                    <div class="oe_kanban_card oe_kanban_global_click">
                        <div class="o_kanban_record_top">
                            <strong><field name="name"/></strong>
                        </div>
                        <div><field name="employee_id"/></div>
                        <div><field name="hours"/> hours on <field name="date"/></div>
                    </div>
                </t>
            </templates>
        </kanban>
    </field>
</record>
```

## Window action

```xml
<record id="action_hr_overtime" model="ir.actions.act_window">
    <field name="name">Overtime Requests</field>
    <field name="res_model">hr.overtime</field>
    <field name="view_mode">list,kanban,form</field>   <!-- v17: list, not tree -->
    <field name="context">{"search_default_my_overtime": 1}</field>
    <field name="domain">[]</field>
    <field name="help" type="html">
        <p class="o_view_nocontent_smiling_face">Create your first overtime request</p>
        <p>Overtime requests need manager approval before counting toward payroll.</p>
    </field>
</record>
```

## Menu

```xml
<menuitem id="menu_hr_overtime_root" name="Overtime" parent="hr.menu_hr_root" sequence="50"/>
<menuitem id="menu_hr_overtime_requests" name="Requests"
          parent="menu_hr_overtime_root" action="action_hr_overtime" sequence="10"/>
```

## View inheritance

```xml
<record id="view_res_partner_form_inherit_overtime" model="ir.ui.view">
    <field name="name">res.partner.form.inherit.overtime</field>
    <field name="model">res.partner</field>
    <field name="inherit_id" ref="base.view_partner_form"/>
    <field name="arch" type="xml">

        <!-- Add a button after an existing one -->
        <xpath expr="//div[@name='button_box']" position="inside">
            <button class="oe_stat_button" type="object" name="action_view_overtimes"
                    icon="fa-clock-o">
                <field name="overtime_count" widget="statinfo" string="Overtimes"/>
            </button>
        </xpath>

        <!-- Replace an attribute -->
        <xpath expr="//field[@name='email']" position="attributes">
            <attribute name="required">True</attribute>
        </xpath>

        <!-- Add a field after another -->
        <field name="phone" position="after">
            <field name="overtime_alert"/>
        </field>

        <!-- Replace, before, after, inside, attributes, move, replace -->
    </field>
</record>
```

### `position` values

- `inside` (default for tags), `before`, `after`, `replace`, `attributes`, `move`.
- Use `<field name="X" position="...">` shorthand when matching by field name.

## Server actions and automated actions

Server actions are scriptable actions stored in `ir.actions.server`, runnable from buttons, menus, or automations.

```xml
<record id="action_hr_overtime_bulk_approve" model="ir.actions.server">
    <field name="name">Approve Selected</field>
    <field name="model_id" ref="model_hr_overtime"/>
    <field name="binding_model_id" ref="model_hr_overtime"/>  <!-- shows in Action menu -->
    <field name="state">code</field>
    <field name="code">
records.filtered(lambda r: r.state == 'submitted').action_approve()
    </field>
</record>
```

## Common pitfalls

- Using `<tree>` in v17 — works via shim but pylint-odoo / OCA CI will reject it.
- Using `attrs="{...}"` — deprecated, use direct attribute expressions.
- Forgetting `inherit_id` on inherited views — creates a duplicate, not an extension.
- `xpath` matching too narrowly (e.g. by sibling order) — fragile across minor versions; match by field name or attribute when possible.
- Putting `groups=` on a button to gate access — that's UI-only. Add a server-side check too.
- `view_mode` listing modes that have no view defined — Odoo will try to auto-generate one (almost never what you want).
- Missing `<field name="state"/>` in kanban when grouping by it — group fails silently.

## References

- [Odoo 17 — Views](https://www.odoo.com/documentation/17.0/developer/reference/backend/views.html)
- [Odoo 17 — Actions](https://www.odoo.com/documentation/17.0/developer/reference/backend/actions.html)
- [Odoo 17 release notes — view changes](https://www.odoo.com/documentation/17.0/administration/upgrade.html)
