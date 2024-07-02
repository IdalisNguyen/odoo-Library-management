# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
'''
Books_data is a model defined in an object-relational mapping (ORM) framework, 
which is often used in Python-based web applications, such as Odoo or Django.
 This class represents a table or collection in a database where information about books is stored.
The _name attribute is used to specify the internal name of the model. In this case, 
it is set to 'books.data',
 which means the table or collection name associated with this model will be 'books_data'.
'''
class Books_data(models.Model):
    _name = 'books.data'
    _description = 'books.dat'

    name = fields.Char(string="Tên Sách", tracking=True)
    price = fields.Float(string="Giá Tiền")
    image = fields.Image(string="Book Cover")
    encode = fields.Char(string="Mã Hóa")
    language = fields.Selection([ ('vn', 'Việt Nam'),('en', 'English'),  ],
                                string='Ngôn Ngữ')
    description = fields.Text(string="Tóm tắt")
    number_of_pages = fields.Char(string="Trang sách")
    size = fields.Char(string="Kích thước")
    author_ids = fields.Many2many('books.author', string="Tác Giả Chính")
    # co_author_ids = fields.Many2many('books.author', string='Tác Giả Phụ')
    distribute = fields.Char(string="Phân loại")
    copy_ids = fields.One2many('book.copies', 'book_id', string='Copies')
    copy_count = fields.Integer(string='Copy Count', compute='_compute_copy_count')
    start_date = fields.Datetime(default=fields.Datetime.today)
    type = fields.Char(string="Loại Hình")
    majors = fields.Char(string="Ngành Học")
    id_module = fields.Char(string="Mã Học Phần")
    module = fields.Char(string="Học Phần")
    """Xuất bản"""
    publisher = fields.Char(string="Nhà Xuất Bản")
    year_of_publication = fields.Char(string="Năm Xuất Bản")
    place_of_publication = fields.Char(string="Nơi Xuất Bản")
    editon = fields.Integer(string="Lần Xuất Bản")
    inventory = fields.Char(string="Kho")
    rack = fields.Many2one("library.rack", "Rack",
        help="Shows position of book")
    back = fields.Selection([("hard", "HardBack"), ("paper", "PaperBack")],
        "Binding Type", help="Shows books-binding type", default="paper")
    library_shelf_id = fields.Many2one('library.shelf', string="Library Shelf")

    # available_quantity = fields.Integer(string='Available Quantity', default="1")

    end_date = fields.Date(string="End Date", store=True,
                           Compute='_get_end_date_', inverse='_set_end_date')
    color = fields.Integer(string="color")
    priority = fields.Selection([('0', 'normal'), ('1', 'low'),
                                 ('2', 'high'),
                                 ('3', 'very high')], string='priority')
    category_ids = fields.Many2one('books.category', string="Category Book")
    key_word = fields.Char(string="Từ Khóa")
    dkcd = fields.Char(string="ĐKCB")
    invoice = fields.Char(string="Invoice")
    note = fields.Char(string="Phụ chú chung")
    isbn = fields.Char(string="ISBN")
    source = fields.Char(string="Nguồn")
    k_h_x_g = fields.Char(string="KHXG")


    state = fields.Selection([
        ('available', 'Available'),
        ('borrowed', 'Borrowed')
    ], string='State', default='available')

    
    @api.depends('copy_ids')
    def _compute_copy_count(self):
        '''
        compute_copy_count: Method decorated with @api.depends('copy_ids').
        This method calculates the value of
         the copy_count field.
         It iterates over each record and sets the copy_count field to the length of the copy_ids field.
        '''
        for book in self:
            # book.copy_count = len(book.copy_ids)
            book.copy_count = str(len(book.copy_ids))

    @api.depends('start_date', 'duration')
    def _get_end_date(self):
        """
            Sets the end date based on the start date and duration.

            This method calculates the end date by adding the duration (in days) to the start date.
            The calculated end date is then assigned to the 'end_date' field of the record.

            If either the start date or duration is not available, the function does nothing.

            Note: This method assumes that the 'start_date' and 'duration' fields are already populated.
            """
        for r in self:
            if not (r.start_date and r.duration):
                r.end_date = r.start_date
                continue

            duration = timedelta(days=r.duration, seconds=-1)
            r.end_date = r.start_date + duration

    def _set_end_date(self):
        for r in self:
            if not (r.start_date and r.duration):
                continue

            r.duration = (r.end_date - r.start_date).days + 1



    @api.onchange("id")
    def _onchange_books_data(self):
        currence = 0
        if self.id:
            currence = self.id.currence.id
        return {"domain": {"currence": [('id' , '=' , currence)]}}








