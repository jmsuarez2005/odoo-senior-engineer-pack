# Odoo 17 — OWL 2 Cheatsheet

## Component skeleton

```js
/** @odoo-module **/

import { Component, useState, useRef, onWillStart, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";

export class MyComponent extends Component {
    static template = "module.MyComponent";
    static props = { record: Object, readonly: { type: Boolean, optional: true } };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({ count: 0 });
        this.inputRef = useRef("input");

        onWillStart(async () => {
            this.state.count = await this.orm.searchCount("res.partner", []);
        });

        onMounted(() => this.inputRef.el?.focus());
    }
}
```

## Hooks

| Hook | Purpose |
|---|---|
| `useState(obj)` | Reactive state |
| `useRef("name")` | DOM ref tagged `t-ref="name"` |
| `useService("name")` | Inject service |
| `onWillStart(fn)` | Async setup before first render |
| `onMounted(fn)` | After DOM mount |
| `onWillUnmount(fn)` | Cleanup |
| `onWillUpdateProps(fn)` | Before props update |

## Common services

```js
const orm = useService("orm");
await orm.searchRead("res.partner", domain, fields, options);
await orm.create("res.partner", [vals]);
await orm.write("res.partner", [id], vals);
await orm.call("res.partner", "method", args, { context });

const notification = useService("notification");
notification.add("Done", { type: "success" });

const dialog = useService("dialog");
dialog.add(SomeDialog, { title: "..." });

const action = useService("action");
action.doAction({ type: "ir.actions.act_window", res_model: "...", ... });
action.doAction("module.xml_id");

const user = useService("user");
console.log(user.userId, user.context);
```

## Registries

```js
registry.category("fields").add("widget_name", { component, supportedTypes: ["char"] });
registry.category("services").add("name", { start, dependencies: [] });
registry.category("actions").add("client_action_tag", Component);
registry.category("systray").add("name", { Component });
registry.category("main_components").add("name", { Component });
```

## Patching

```js
import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";

patch(ListController.prototype, {
    setup() {
        super.setup();
        // additions
    },
});
```

## QWeb-OWL templates (XML)

```xml
<t t-name="module.MyComponent">
    <div class="...">
        <span t-esc="state.count"/>
        <button t-on-click="onClick" t-att-class="state.active ? 'active' : ''">
            <t t-if="state.loading">Loading...</t>
            <t t-else=""><t t-esc="state.label"/></t>
        </button>
        <ul>
            <li t-foreach="state.items" t-as="item" t-key="item.id">
                <t t-esc="item.name"/>
            </li>
        </ul>
        <input t-ref="input"/>
        <ChildComponent record="props.record" t-on-update="onUpdate"/>
    </div>
</t>
```

## Common gotchas

- Forgot `/** @odoo-module **/` → module not registered, silent.
- `await` in `setup()` directly → setup isn't async; use `onWillStart`.
- Mutating `props` → forbidden, use `state`.
- v15/16 `patch(target, "name", overrides)` → drop the name in v17.
- Importing from `web.field_registry` → use `@web/core/registry`.
- Static template not in asset bundle → "template not found" at runtime.
