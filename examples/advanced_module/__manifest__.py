# Copyright 2026 Jean Suarez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Advanced Example: Overtime",
    "version": "17.0.1.0.0",
    "summary": "Reference module: ACLs, record rules, chatter, wizard, OWL widget, REST API, QWeb report",
    "author": "Jean Suarez, Odoo Community Association (OCA)",
    "website": "https://github.com/jmsuarez2005/odoo-senior-engineer-pack",
    "license": "AGPL-3",
    "category": "Human Resources",
    "depends": [
        "base",
        "hr",
        "mail",
    ],
    "data": [
        "security/security_groups.xml",
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        "data/ir_sequence_data.xml",
        "data/mail_template.xml",
        "views/hr_overtime_views.xml",
        "views/menu_views.xml",
        "wizards/hr_overtime_approve_wizard_views.xml",
        "reports/hr_overtime_report.xml",
        "reports/hr_overtime_report_template.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "advanced_module/static/src/js/**/*",
            "advanced_module/static/src/xml/**/*",
            "advanced_module/static/src/scss/**/*",
        ],
    },
    "installable": True,
    "application": True,
}
