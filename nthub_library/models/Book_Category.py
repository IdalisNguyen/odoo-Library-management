# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta as rd

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError as UserError


class Book_Category(models.Model):
    '''
    class category content name of category books
    '''
    _name = 'books.category'
    _description = 'books category'

    name = fields.Char(string="Category")
    rack = fields.Many2many()


    library_rack_ids = fields.Many2many('library.rack', 'rack',
                                  'shelf_id', 'rack_id', string="rack")
    # library_shelf_ids = fields.Many2many('library.shelf', 'library_rack_shelf_rel',
    #                           'shelf_id', 'rack_id', string="Shelf")


class LibraryBookShelf(models.Model):
    """Defining Library Shelf."""

    _name = "library.shelf"
    _description = "Library Shelf"

    name = fields.Char(string="Name")

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
        """
        We override the _search because we need to show the shelf
        according to the domain.
        """
        if 'library_shelf_domain' in self._context:
            domain_id = self.env["library.rack"].browse(self._context.get('library_shelf_domain'))
            shelf_ids = domain_id.library_shelf_ids
            if self.env.context.get('count'):
                return len(shelf_ids)
            return shelf_ids.ids
        return super(LibraryBookShelf, self)._search(args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)

class LibraryRack(models.Model):
    """Defining Library Rack."""

    _name = "library.rack"
    _description = "Library Rack"

    name = fields.Char("Name", required=True, help="Rack Name")
    code = fields.Char("Code", help="Enter code here")
    active = fields.Boolean("Active", default="True",
        help="To active/deactive record")
    library_shelf_ids = fields.Many2many('library.shelf', 'library_rack_shelf_rel',
                                  'shelf_id', 'rack_id', string="Shelf")

    @api.constrains("library_shelf_ids")
    def check_shelf(self):
        """Constraint to assign library card more than once"""
        if self.search([("id", "not in", self.ids),
                ("library_shelf_ids", "in", self.library_shelf_ids.ids)]):
            raise UserError(_("""Library shelf already assigned for another rank!"""))


