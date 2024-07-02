# -*- coding: utf-8 -*-
from datetime import timedelta, datetime, date
from odoo import models, fields, api , _
from odoo.exceptions import ValidationError as UserError
import cv2
import re
from pyzbar.pyzbar import decode
from datetime import datetime


from odoo import http
from odoo.http import request
'''
The Borrows class represents a model for book borrowings in the context of an application built using the Odoo framework. 
It extends the models.Model class, which is the base class for all Odoo models.
The _name attribute is used to specify the internal name of the model. In this case,
the internal name is set to 'books.borrows'.
This name is used to identify the model in the database and in various places within the Odoo framework.
The _description attribute provides a description for the model. In this case, it is set to 'books.borrows'.
The class defines several fields that represent different aspects of a book borrowing
'''
class Borrows(models.Model):
    _name = 'books.borrows'
    _description = 'books.borrows'

    name = fields.Many2one('res.partner', string="Name")
    # name = fields.Many2one('library.card', string="Name")
    code = fields.Many2one('library.card', string='Library Card')
    name_card = fields.Many2one('res.partner', related='code.student_id', string="Borrower")
    id_student = fields.Char(string="ID Student", size=256, related='code.id_student',readonly=True)
    # library_card = fields.Char(string="Library Card", size=256,related='code.code',readonly=True)


    # book_id = fields.Many2one('books.data', string='Book', readonly=True)
    book_id = fields.Many2one('books.data', string='Book', readonly=True)
    borrow_ids = fields.Many2many('books.data', 'book_id', string='Books')

    start_borrow = fields.Datetime(string="Start Borrow", default=lambda self: fields.Datetime.now())
    state = fields.Selection([('draft', 'Draft'),
                              ('running', 'Running'),
                              ('delayed', 'Delayed'),
                              ('ended', 'Ended'),
                              ], default="draft", string='state')
    end_borrow = fields.Datetime(string="End Borrow", store=True,
                                 compute='_get_end_date_', inverse='_set_end_date')

    daily_price = fields.Float(string="Day Price", related='book_id.price')
    color = fields.Integer()
    duration = fields.Integer()
    received_date = fields.Datetime()
    delay_duration = fields.Float(string="Delay Duration", readonly=True)
    delay_penalties = fields.Many2one('delay.penalities', string="Delay Penalties")
    borrows_duration = fields.Float(string="Borrows Duration")
    sub_total = fields.Integer(compute='_compute_sub_s_total', store=True)
    total_money = fields.Float(compute='_compute_total', store=True, string="Total Money")
    book_copy_id = fields.Many2one('book.copies', string="Copies")
    book_copy_list = fields.Many2one('book.copies')
    partner_id = fields.Many2one('res.partner', string='Partner')
    place = fields.Char(related="book_copy_id.place")

    #note
    quantity = fields.Integer(string='Quantity', default = "1")
    # borrow_id = fields.Char(string='Borrow ID', required=True, copy=False, readonly=True, index=True, default=lambda self: ())
    # borrow_id = fields.Char(string='Borrow ID', store=True, required=True, readonly=True, default=lambda self: self._default_borrow_id())
    borrow_id = fields.Char(string='Borrow ID', compute='_default_borrow_id', store=True)
    return_date = fields.Date(string='Return Date')


    # search borrower
    @api.model
    def process_qr_scan(self):
        # Giả sử action_scan_qr_return_borrow trả về book_id
        book_id = self.action_scan_qr_return_borrow()
        if book_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Tìm kiếm theo ID sách',
                'res_model': 'books.borrows',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'target': 'current',
                'domain': [('book_id.dkcd', '=', book_id)],
                'context': {'default_book_id.dkcd': book_id}
            }
        else:
            return {
                'type': 'ir.actions.act_window_close'
            }
    def action_scan_qr_return_borrow(self):
        a = 10
        # Mở camera
        cap = cv2.VideoCapture(0)

        # Kiểm tra xem camera có được mở không
        if not cap.isOpened():
            print("Không thể mở camera. Hãy chắc chắn rằng không có ứng dụng khác sử dụng camera.")
            return
        # Lặp để hiển thị hình ảnh từ camera
        while True:
            # Đọc frame từ camera
            ret, frame = cap.read()

            # Hiển thị frame
            cv2.imshow('Camera', frame)

            # Quét mã QR
            decoded_objects = decode(frame)
            for obj in decoded_objects:
                qr_data = obj.data.decode('utf-8')
                
                print(f'Mã QR đã quét: \n{qr_data}')
                # match = re.search(r'(\d+)', qr_data)
                # match = re.search(r'(\d+)', qr_data)
                match = re.search(r'(.+)', qr_data)

                if match:
                    book_id = match.group(1).strip()
                    print(f"Id scaned {book_id}")
                    return book_id
                return False

                    
                # Sử dụng regex để trích xuất số từ dòng có tên là "QR Code:"
                # match = re.search(r'QR Code: (\d+)', qr_data)
                # Giải phóng camera và đóng cửa sổ hiển thị
                cap.release()
                cv2.destroyAllWindows()

                # Kết thúc chương trình sau khi quét được mã QR
                return
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        # Giải phóng camera và đóng cửa sổ hiển thị khi thoát vòng lặp
        cap.release()
        cv2.destroyAllWindows()        

    borrow_sequence = fields.Integer(string='Borrow Sequence', readonly=True)

    @api.depends('id_student', 'book_id')
    def _default_borrow_id(self):
        if self.id_student:
            student_id = self.id_student
            book_id = self.book_id.id
            # print(f"id sach: {book_id}")
            borrow_count = self.search_count([('id_student', '=', student_id), ('book_id', '=', book_id)])
            self.borrow_id = '{}_{}_{}'.format(student_id,book_id, borrow_count + 1)
        else:
            # Set a placeholder or temporary value for borrow_id when complete data isn't available.
            self.borrow_id = 'Incomplete_Info'



    # @api.model
    # def _default_borrow_id(self):
    #     # Tìm giao dịch mượn trước đó cho cùng sinh viên và sách.
    #     previous_borrows = self.env['books.borrows'].search([
    #         ('name', '=', self.name.id),
    #         ('book_id', '=', self.book_id.id)
    #     ], order='create_date desc')

    #     # Tính toán số lần mượn mới bằng cách đếm các giao dịch trước đó + 1.
    #     borrow_count = len(previous_borrows) + 1
        
    #     # Tạo borrow_id mới dựa trên id_student, book_id và số lần mượn.
    #     return f"{self.id_student}_{self.book_id.id}_{borrow_count:03d}"


    def action_report(self):
        # function to report wornning
        return self.env.ref('nthub_library.report_borrows_warning_id').report_action(self)

    @api.model
    def create(self, vals):
        records = super(Borrows, self).create(vals)
        if 'start_borrow' not in vals:
            vals['start_borrow'] = fields.Datetime.now()
        if 'end_borrow' in vals and vals['end_borrow'] == vals.get('start_borrow'):
            vals['end_borrow'] = None  # Or handle it in a way that suits your logic
        if 'id_student' in vals and 'book_id' in vals:
            student_id = vals['id_student']
            book_id = vals['book_id']  # This should be the ID directly from `vals`
            borrow_count = self.env['books.borrows'].search_count([
                ('id_student', '=', student_id),
                ('book_id', '=', book_id)
            ])
            vals['borrow_id'] = f'{student_id}_{book_id}_{borrow_count + 1}'
        else:
            vals['borrow_id'] = 'New'
            """ update state book"""
        for record in records.borrow_ids:
            if record.state == 'borrowed':
                raise UserError(f'The book {record.dkcd} is already borrowed.')
            record.state = 'borrowed'
        return records



    @api.onchange('start_borrow', 'end_borrow')
    def states_test(self):
        # when sdate <= today <= edate state=running else state=draft
        sdate = self.start_borrow
        edate = self.end_borrow
        today = datetime.now()
        if sdate and edate:
            if sdate <= today <= edate:
                self.state = 'running'
                # if self.book_id:
                #     self.book_id.available_quantity -= self.quantity
                self.book_id.state = 'borrowed'
                self.borrow_ids.state = 'borrowed'
            else:
                self.state = 'draft'
        else:
            self.state = 'draft'

    @api.onchange('borrows_duration')
    def _onchange_borrows_duration(self):
        #
        if self.borrows_duration and self.start_borrow:
            start_date = fields.Datetime.from_string(self.start_borrow)
            new_end_date = start_date + timedelta(days=self.borrows_duration)
            self.end_borrow = new_end_date

    @api.onchange('start_borrow', 'end_borrow')
    def _onchange_da_tes(self):
        '''
                to calculate period of borrows Duration based on start deta and end date
        '''
        if self.start_borrow and self.end_borrow:
            delta = self.end_borrow - self.start_borrow
            if delta.days < 0:
                nod = 0
            else:
                nod = delta.days
            self.borrows_duration = nod
        else:
            self.borrows_duration = 0

    @api.onchange('book_copy_id')
    def _onchange_book_copy_id(self):
        # function depend on book_copies
        # if customer take copy available can change in the model book_copies state = borrowed
        if self.book_copy_id and self.book_copy_id.state == 'available':
            self.book_copy_id.state = 'borrowed'

    @api.depends('start_borrow', 'duration')
    def _get_end_date_(self):
        '''
        This method is decorated with @api.depends('start_borrow', 'duration'), which means it will be automatically triggered and recompute the field end_borrow whenever the start_borrow or duration fields are modified.
It iterates over each record (r) in the current recordset (self).
Inside the loop, it checks if both start_borrow and duration fields are set (if not (r.start_borrow and r.duration)).
If either start_borrow or duration is not set, it sets the end_borrow field to the value of start_borrow and continues to the next record (continue).
If both start_borrow and duration are set, it calculates the duration in days as a timedelta object using the timedelta function and subtracting one second (duration = timedelta(days=r.duration, seconds=-1)).
Finally, it sets the end_borrow field by adding the duration to the start_borrow (r.end_borrow = r.start_borrow + duration).
        '''
        for r in self:
            if not (r.start_borrow and r.duration):
                r.end_borrow = r.start_borrow
                continue
            duration = timedelta(days=r.duration, seconds=-1)
            r.end_borrow = r.start_borrow + duration

    def _set_end_date(self):
        for r in self:
            if not (r.start_borrow and r.duration):
                continue

            r.duration = (r.end_borrow - r.start_borrow).days + 1

    def action_ended(self):

        """
         Perform the action of change the borrow to the 'ended' state.
       """
        self.received_date = datetime.now().strftime('%Y-%m-%d')
        self.state = 'ended'
        self.book_copy_id.state = 'available'
        for record in self:
            for book in record.borrow_ids:
                book.state = 'available'
            record.state = 'ended'
            record.return_date = fields.Date.today()



    def action_draft(self):
        # button to reset to draft
        # for rec in self:
        #     rec.state = 'draft'
        for rec in self:
            # Kiểm tra xem bản ghi có trong trạng thái 'ended' không
            if rec.state == 'ended':
                # Gọi phương thức create để tạo một bản ghi mới
                new_record = rec.create({
                    'book_id': rec.book_id.id,
                    'id_student': rec.id_student,
                    'start_borrow': rec.start_borrow,
                    'borrow_id': rec.borrow_id,
                    'end_borrow': rec.end_borrow,
                })
                # Đặt trạng thái của bản ghi mới là 'draft'
                new_record.state = 'draft'
                # Xóa bản ghi hiện tại
                rec.unlink()
            else:
                raise UserError('Không thể đặt lại về dạng nháp. Bản ghi không ở trạng thái "ended".')
    # @api.constrains('quantity')
    # def _check_quantity(self):
    #     for record in self:
    #         if record.quantity <= 0:
    #             raise UserError("Quantity must be a positive number.")


    @api.onchange('book_id')
    def _onchange_book_id(self):
        '''  Perform a search to find available copies of the selected book
            Return a domain filter to restrict the available options for the book_copy_id field
        '''
        book_copies = self.env['book.copies'].search(
            [("book_id", "=", self.book_id.id), ('state', '=', 'available')]).ids
        self.book_copy_id = False
        self.book_copy_list = [(6, 0, book_copies)]





    @api.onchange('end_borrow', 'received_date')
    def onchange_dates(self):
        '''
        to calculate delay_duration based on end_borrow and received_date
         delay_duration = received_date - end_borrow
        '''
        if self.end_borrow and self.received_date:
            delta = self.received_date - self.end_borrow
            if delta.days < 0:
                nod = 0
            else:
                nod = delta.days
            self.delay_duration = nod
        else:
            self.delay_duration = 0

    @api.depends('daily_price', 'borrows_duration')
    def _compute_sub_s_total(self):
        '''
        to calculate sub_total based on (daily_price) and (borrows_duration)
        daily_price * borrows_duration =sub_total
        '''
        for rec in self:
            sub_total = 0.0
            if rec.borrows_duration and rec.daily_price:
                sub_total = rec.borrows_duration * rec.daily_price
            rec.sub_total = sub_total



    @api.depends('sub_total', 'delay_penalties')
    def _compute_total(self):
        '''
        to calculate total money of period borrowed user
        based on sub_total and delay_penalties
        '''
        for rec in self:
            total_money = 0.0
            if rec.sub_total and rec.delay_penalties:
                total_money = rec.sub_total + rec.delay_penalties
            rec.total_money = total_money

    # cron jop
    def update_delayed_status(self):
        # cron job every day to check state =running $ end_borrow < date today  change state from running to delayed
        today = date.today()
        running_borrows = self.env['books.borrows'].search([('state', '=', 'running'), ('end_borrow', '<', today)])
        for rec in running_borrows:
            if rec:
                rec.state = 'delayed'

    """ Scan name student """
    def action_scan_name_student(self, vals):
        # Mở camera
        cap = cv2.VideoCapture(0)

        # Kiểm tra xem camera có được mở không
        if not cap.isOpened():
            print("Không thể mở camera. Hãy chắc chắn rằng không có ứng dụng khác sử dụng camera.")
            return
        # Lặp để hiển thị hình ảnh từ camera
        while True:
            # Đọc frame từ camera
            ret, frame = cap.read()

            # Hiển thị frame
            cv2.imshow('Camera', frame)

            # Quét mã QR
            decoded_objects = decode(frame)
            for obj in decoded_objects:
                qr_data = obj.data.decode('utf-8')
                
                print(f'Mã QR đã quét: \n{qr_data}')
                # match = re.search(r'Id Student: (\d+)', qr_data)
                # if match:
                #     qr_code_name = int(match.group(1))
                match = re.search(r'Student Card: (.+)', qr_data)
                if match:
                    qr_code_content = match.group(1).strip()                
                    print(f'Library Card of Student: {qr_code_content}')

                    # qr_code = qr_code_number()  # Assume this function returns the scanned QR code

                    # Find the book with the scanned QR code
                    name_borrower = self.env['library.card'].search([('code', '=', qr_code_content)])

                    # If book is found, fill the qbook_id field
                    if name_borrower:
                        self.code = name_borrower.id
                        print()
                    else:
                        # Handle case when book is not found
                        pass
                # Sử dụng regex để trích xuất số từ dòng có tên là "QR Code:"
                # match = re.search(r'QR Code: (\d+)', qr_data)
                # Giải phóng camera và đóng cửa sổ hiển thị
                cap.release()
                cv2.destroyAllWindows()

                # Kết thúc chương trình sau khi quét được mã QR
                return

            # Kiểm tra phím nhấn để thoát (ví dụ: nhấn phím 'q')
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Giải phóng camera và đóng cửa sổ hiển thị khi thoát vòng lặp
        cap.release()
        cv2.destroyAllWindows()

    """ Scan barcode student """
    def action_barcode_name_student(self, vals):
        # Mở camera
        cap = cv2.VideoCapture(0)

        # Kiểm tra xem camera có được mở không
        if not cap.isOpened():
            print("Không thể mở camera. Hãy chắc chắn rằng không có ứng dụng khác sử dụng camera.")
            return

        # Lặp để hiển thị hình ảnh từ camera
        while True:
            # Đọc frame từ camera
            ret, frame = cap.read()

            # Hiển thị frame
            cv2.imshow('Camera', frame)

            # Quét mã Barcode
            decoded_objects = decode(frame)
            for obj in decoded_objects:
                barcode_data = obj.data.decode('utf-8')
                
                print(f'Mã Barcode đã quét: \n{barcode_data}')
                match = re.search(r'(\d+)', barcode_data)
                if match:
                    barcode_name = int(match.group(1))
                    print(f'ID Student Barcode: {barcode_name}')

                    # Find the student with the scanned Barcode
                    student = self.env['res.partner'].search([('id_student', '=', barcode_name)],limit = 1)

                    # If student is found, fill the student_id field
                    if student:
                        self.name = student.id
                        self.code = self.env['library.card'].search([('student_id', '=', student.id)], limit=1).id
                        print(f'Student ID: {self.name_card}')
                    else:
                        # Handle case when student is not found
                        print('Student not found.')
                        pass

                    # Giải phóng camera và đóng cửa sổ hiển thị
                    cap.release()
                    cv2.destroyAllWindows()

                    # Kết thúc chương trình sau khi quét được mã Barcode
                    return

            # Kiểm tra phím nhấn để thoát (ví dụ: nhấn phím 'q')
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Giải phóng camera và đóng cửa sổ hiển thị khi thoát vòng lặp
        cap.release()
        cv2.destroyAllWindows()



    def action_scan_qr(self, vals):
        # Mở camera
        cap = cv2.VideoCapture(0)

        # Kiểm tra xem camera có được mở không
        if not cap.isOpened():
            print("Không thể mở camera. Hãy chắc chắn rằng không có ứng dụng khác sử dụng camera.")
            return
        # Lặp để hiển thị hình ảnh từ camera
        while True:
            # Đọc frame từ camera
            ret, frame = cap.read()

            # Hiển thị frame
            cv2.imshow('Camera', frame)

            # Quét mã QR
            decoded_objects = decode(frame)
            for obj in decoded_objects:
                qr_data = obj.data.decode('utf-8')
                
                match = re.search(r'(.+)', qr_data)
                if match:
                    qr_code_number = match.group(1).strip() 


                    print(f'ID QR Code: {qr_code_number}')

                    # qr_code = qr_code_number()  # Assume this function returns the scanned QR code

                    # Find the book with the scanned QR code
                    book = self.env['books.data'].search([('dkcd', '=', qr_code_number)])

                    # If book is found, fill the qbook_id field
                    if book:
                        self.book_id = book.id
                        self.borrow_ids = [(4, book.id)]
                        if book.state == 'borrowed':
                            raise UserError('This book is already borrowed.')
                        book.state = 'available'
                    
                    else:
                        # Handle case when book is not found
                        pass
                # Sử dụng regex để trích xuất số từ dòng có tên là "QR Code:"
                # match = re.search(r'QR Code: (\d+)', qr_data)
                # Giải phóng camera và đóng cửa sổ hiển thị
                cap.release()
                cv2.destroyAllWindows()

                # Kết thúc chương trình sau khi quét được mã QR
                return

            # Kiểm tra phím nhấn để thoát (ví dụ: nhấn phím 'q')
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Giải phóng camera và đóng cửa sổ hiển thị khi thoát vòng lặp
        cap.release()
        cv2.destroyAllWindows()


class ResPartner(models.Model):
    _inherit = 'res.partner'

    borrow_ids = fields.One2many('books.borrows', 'name_card', string='Books')
    card_no = fields.One2many('library.card','student_id', string='Library Card')    
    # library_card_code = fields.Char(related='card_no.code', string='Library Card Code')


# class Resuser(models.Model):
#     _inherit = 'res.users'

#     id = fields.Many2one()
#     # library_card_code = fields.Char(related='card_no.code', string='Library Card Code')
