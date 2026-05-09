# Copyright 2026 Jean Suarez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Minimal Example",
    "version": "17.0.1.0.0",
    "summary": "Smallest valid Odoo 17 module — one model, ACL, views",
    "author": "Jean Suarez, Odoo Community Association (OCA)",
    "website": "https://github.com/jmsuarez2005/odoo-senior-engineer-pack",
    "license": "AGPL-3",
    "category": "Tools",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "views/minimal_book_views.xml",
    ],
    "installable": True,
    "application": False,
}
