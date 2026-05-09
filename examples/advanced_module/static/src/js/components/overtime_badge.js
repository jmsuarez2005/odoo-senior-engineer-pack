/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

class OvertimeBadge extends Component {
    static template = "advanced_module.OvertimeBadge";
    static props = { ...standardFieldProps };

    setup() {
        this.orm = useService("orm");
        this.state = useState({ count: 0, loading: true });

        onWillStart(async () => {
            const recordId = this.props.record.resId;
            if (recordId) {
                this.state.count = await this.orm.searchCount(
                    "hr.overtime",
                    [["employee_id", "=", recordId], ["state", "=", "submitted"]],
                );
            }
            this.state.loading = false;
        });
    }
}

registry.category("fields").add("overtime_badge", {
    component: OvertimeBadge,
    supportedTypes: ["integer"],
});
