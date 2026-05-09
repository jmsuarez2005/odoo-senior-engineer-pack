---
name: owl-frontend
description: Build Odoo 17 OWL 2 components, services, hooks, registries, and custom field/view widgets. Use when writing JS for the Odoo web client — components in static/src/js, asset bundles, OWL templates in static/src/xml.
---

# OWL Frontend (Odoo 17)

## When to use this skill

You're writing JS that runs in the Odoo web client. New widget, custom view, dashboard component, custom button, anything in `static/src/`. Odoo 17 uses **OWL 2** — different from the OWL 1 in v15 and earlier.

## OWL 2 essentials

OWL is a thin reactive component framework. Every component is a JS class extending `Component`. State is reactive via `useState`. Templates are XML referenced by `static template`.

```js
/** @odoo-module **/

import { Component, useState, onWillStart, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";

export class OvertimeBadge extends Component {
    static template = "hr_overtime.OvertimeBadge";
    static props = {
        record: Object,
        readonly: { type: Boolean, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({ count: 0, loading: true });

        onWillStart(async () => {
            this.state.count = await this.orm.searchCount(
                "hr.overtime",
                [["employee_id", "=", this.props.record.resId], ["state", "=", "submitted"]],
            );
            this.state.loading = false;
        });
    }

    onClick() {
        this.notification.add("Opening overtime list", { type: "info" });
    }
}
```

The XML template:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<templates xml:space="preserve">

    <t t-name="hr_overtime.OvertimeBadge">
        <span class="badge text-bg-info" t-on-click="onClick">
            <t t-if="state.loading">…</t>
            <t t-else=""><t t-esc="state.count"/> pending</t>
        </span>
    </t>

</templates>
```

## File layout

```
static/src/
├── js/
│   ├── components/
│   │   └── overtime_badge.js
│   └── views/
│       └── overtime_list_view.js
├── xml/
│   └── overtime_badge.xml
└── scss/
    └── overtime.scss
```

Asset bundle declaration in `__manifest__.py`:
```python
"assets": {
    "web.assets_backend": [
        "hr_overtime/static/src/**/*.js",
        "hr_overtime/static/src/**/*.xml",
        "hr_overtime/static/src/**/*.scss",
    ],
},
```

Bundle reference:
- `web.assets_backend` — the backend (logged-in client)
- `web.assets_frontend` — public website / portal
- `web.assets_qweb` — QWeb-rendered chunks
- `web.assets_tests` — test utilities (only loaded with `--test-tags`)

## Hooks (the v17 ones you'll use)

| Hook | When |
|---|---|
| `useState(obj)` | Reactive state object |
| `useRef("name")` | Reference DOM node tagged `t-ref="name"` |
| `useService("name")` | Inject a service (orm, notification, dialog, action, …) |
| `onWillStart(fn)` | Async setup before first render |
| `onMounted(fn)` | After mount (DOM available) |
| `onWillUnmount(fn)` | Before unmount (cleanup) |
| `onWillUpdateProps(fn)` | Before props update |
| `useEnv()` | Access component env (rare) |

## Services — the most common ones

```js
const orm = useService("orm");                  // ORM RPC
await orm.read("res.partner", [1, 2], ["name", "email"]);
await orm.searchRead("res.partner", [["active", "=", true]], ["name"]);
await orm.create("res.partner", [{ name: "Foo" }]);
await orm.write("res.partner", [1], { name: "Bar" });
await orm.unlink("res.partner", [1]);
await orm.call("res.partner", "custom_method", [args], { context: ctx });

const notification = useService("notification");
notification.add("Saved", { type: "success" });

const dialog = useService("dialog");
dialog.add(ConfirmationDialog, { title: "Delete?", body: "..." });

const action = useService("action");
action.doAction({ type: "ir.actions.act_window", res_model: "hr.overtime", ... });
action.doAction("hr_overtime.action_hr_overtime");

const router = useService("router");
const user = useService("user");
console.log(user.userId, user.name, user.context);
```

## Registries

Anything that can be "swapped" in Odoo lives in a registry — fields, views, actions, services, components.

```js
import { registry } from "@web/core/registry";

// Custom field widget
import { CharField } from "@web/views/fields/char/char_field";
class UppercaseCharField extends CharField {
    static template = "hr_overtime.UppercaseCharField";
    onChange(ev) {
        return super.onChange({ ...ev, target: { value: ev.target.value.toUpperCase() } });
    }
}
registry.category("fields").add("uppercase_char", {
    component: UppercaseCharField,
    supportedTypes: ["char"],
});
```

Use it from XML:
```xml
<field name="reference" widget="uppercase_char"/>
```

### Common registries

| Category | What goes in |
|---|---|
| `services` | App-wide services |
| `fields` | Field widgets |
| `views` | View types |
| `view_widgets` | Generic view widgets |
| `actions` | Action handlers (client actions) |
| `main_components` | Always-mounted UI (chatter, command palette, …) |
| `systray` | Top-bar icons |

## Patching existing components

Use `patch` from `@web/core/utils/patch`:

```js
import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";

patch(ListController.prototype, {
    setup() {
        super.setup();
        // your additions
    },

    onDeleteSelectedRecords() {
        if (!confirm("Are you sure?")) return;
        return super.onDeleteSelectedRecords(...arguments);
    },
});
```

In v17, `patch` no longer takes a name as its first argument — that's a v15/16 signature change. Just `patch(target, overrides)`.

## A complete custom client action

```js
/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class OvertimeDashboard extends Component {
    static template = "hr_overtime.OvertimeDashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.state = useState({ pending: 0, approved: 0, hours: 0 });
        this.load();
    }

    async load() {
        const [pending, approved] = await Promise.all([
            this.orm.searchCount("hr.overtime", [["state", "=", "submitted"]]),
            this.orm.searchCount("hr.overtime", [["state", "=", "approved"]]),
        ]);
        this.state.pending = pending;
        this.state.approved = approved;
    }
}

registry.category("actions").add("hr_overtime.dashboard", OvertimeDashboard);
```

Register the client action in XML:
```xml
<record id="action_hr_overtime_dashboard" model="ir.actions.client">
    <field name="name">Overtime Dashboard</field>
    <field name="tag">hr_overtime.dashboard</field>
</record>
```

And a menu pointing to it:
```xml
<menuitem id="menu_hr_overtime_dashboard" name="Dashboard"
          parent="menu_hr_overtime_root"
          action="action_hr_overtime_dashboard" sequence="5"/>
```

## SCSS

```scss
// hr_overtime/static/src/scss/overtime.scss
.o_overtime_badge {
    background-color: var(--bs-info);
    color: white;
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;

    &.o_pending {
        background-color: var(--bs-warning);
    }
}
```

Variables come from Bootstrap 5 (`--bs-*`). Don't hardcode colors — respect dark mode.

## Common pitfalls

- Forgetting `/** @odoo-module **/` at the top of the JS file — module not registered, silent failure.
- Using v15/v16 OWL 1 syntax (`tags = "owl"`, `useState({ ... })` outside `setup`) — OWL 2 is stricter.
- Modifying `props` directly — props are immutable. Mirror to `state` if you need to mutate.
- Awaiting in `setup()` directly — use `onWillStart`. `setup` itself isn't awaited.
- Defining props without a static `props` declaration — OWL warns / breaks. Use `static props = ["*"]` to accept anything if you really mean it.
- Importing from `web.field_registry` — that's v15 path. Use `@web/core/registry` and `registry.category("fields")`.
- Passing `name` to `patch()` — that's the old API. v17 is `patch(target, { method() {}, ... })`.
- Registering a service with `serviceRegistry.add` directly — use `registry.category("services").add("name", { start, dependencies })`.
- Forgetting to add the XML to the asset bundle — template not found at runtime.

## References

- [Odoo 17 — JavaScript reference](https://www.odoo.com/documentation/17.0/developer/reference/frontend/javascript_reference.html)
- [Odoo 17 — OWL framework](https://www.odoo.com/documentation/17.0/developer/reference/frontend/owl_components.html)
- [Odoo 17 — Registries](https://www.odoo.com/documentation/17.0/developer/reference/frontend/registries.html)
- [Odoo 17 — Hooks](https://www.odoo.com/documentation/17.0/developer/reference/frontend/hooks.html)
- [OWL upstream docs](https://github.com/odoo/owl/tree/master/doc)
