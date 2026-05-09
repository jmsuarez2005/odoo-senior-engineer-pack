# Copyright 2026 Jean Suarez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMinimalBook(TransactionCase):

    def test_create_book(self):
        book = self.env["minimal.book"].create({
            "title": "Foundation",
            "author": "Asimov",
            "pages": 244,
            "tag": "fiction",
        })
        self.assertEqual(book.title, "Foundation")
        self.assertFalse(book.is_thick)

    def test_thick_book_compute(self):
        book = self.env["minimal.book"].create({"title": "War and Peace", "pages": 1225})
        self.assertTrue(book.is_thick)
        book.pages = 200
        self.assertFalse(book.is_thick)
