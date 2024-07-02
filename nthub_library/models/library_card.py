# -*- coding: utf-8 -*-
from datetime import timedelta, datetime, date
from odoo import models, fields, api , _
from odoo.exceptions import ValidationError as UserError
import cv2
import re
from pyzbar.pyzbar import decode
from datetime import datetime
from dateutil.relativedelta import relativedelta as rd



class LibraryCard(models.Model):
    """Defining Library Card."""

    _name = "library.card"
    _description = "Library Card information"
    _rec_name = "code"

    @api.depends("student_id")
    def _compute_name(self):
        """Compute name"""
        for rec in self:
            if rec.student_id:
                user = rec.student_id.name
            user = rec.teacher_id.name
            rec.card_name = user

    @api.depends("start_borrow", "duration")
    def _compute_end_borrow(self):
        for rec in self:
            if rec.start_borrow:
                rec.end_borrow = rec.start_borrow + rd(months=rec.duration)

    # def compute_book_issue_count(self):
    #     """Count the book issue based on card.

    #     Returns:
    #         number: return the number of book issued.
    #     """
    #     for rec in self:
    #         rec.book_issue_count = self.env['library.book.issue'].search_count([
    #             ("card_id", "=", self.id)
    #         ])

    code = fields.Char("Card No", required=True, default=lambda self: _("New"),
        help="Enter card number")
    book_limit = fields.Integer("No Of Book Limit On Card", required=True,
        help="Enter no of book limit")
    user_id = fields.Many2one('res.users',"student login user")
    # id_user =  fields.Many2one('res.users',"student login user")
    """note"""
    student_id = fields.Many2one("res.partner", "Student Name",
        help="Select related student")
    email = fields.Char(string='Email Borrower', size=256, related='student_id.email', readonly=True)
    phone_number = fields.Char(string="Phone Number", related='student_id.phone', readonly=True)
    # standard_id = fields.Many2one("school.standard", "Standard",
    #     help="Select standard")
    card_name = fields.Char(compute="_compute_name", string="Card Name",
        help="Card name")
    user = fields.Selection([("student", "Student"), ("teacher", "Teacher")],
        "User", help="Select user")
    state = fields.Selection([('draft', 'Draft'),
                              ('running', 'Running'),
                              ('ended', 'Ended'),
                              ], default="draft", string='state')
    # roll_no = fields.Integer("Roll No", help="Enter roll no.")

    id_student = fields.Char(string="Student ID", help="ID of the student from res.partner")
    
    teacher_id = fields.Many2one("res.partner", "Teacher Name")
    start_borrow = fields.Date("Start Date", default=fields.Date.context_today,
        help="Enter start date")
    duration = fields.Integer("Duration", help="Duration in months")
    end_borrow = fields.Date("End Date", compute="_compute_end_borrow",
        store=True, help="End date")
    active = fields.Boolean("Active", default=True,
        help="Activate/deactivate record")
    book_issue_count = fields.Integer(compute="compute_book_issue_count",
                                      string="Book Issue Count")
    
    borrow_ids = fields.One2many('books.borrows', 'code')



    # @api.onchange("student_id")
    # def on_change_student(self):
    #     """  This method automatically fill up student roll number
    #          and standard field  on student_id field
    #     @student : Apply method on this Field name
    #     @return : Dictionary having identifier of the record as key
    #         and the value of student roll number and standard"""
    #     if self.student_id:
    #         self.standard_id = self.student_id.standard_id.id
    #         self.roll_no = self.student_id.roll_no

    @api.model
    def create(self, vals):
        if vals.get('student_id'):
            student_rec = self.env['res.partner'].browse(vals.get('student_id'))
            vals['id_student'] = student_rec.id_student
        return super(LibraryCard, self).create(vals)

    def write(self, vals):
        if vals.get('student_id'):
            student_rec = self.env['res.partner'].browse(vals.get('student_id'))
            vals['id_student'] = student_rec.id_student
        return super(LibraryCard, self).write(vals)

    @api.constrains("student_id", "teacher_id")
    def check_member_card(self):
        """Constraint to assign library card more than once"""
        if self.user == "student":
            if self.search([
                    ("student_id", "=", self.student_id.id),
                    ("id", "not in", self.ids),
                    ("state", "!=", "expire")]):
                raise UserError(_(
"""You cannot assign library card to same student more than once!"""))
        if self.user == "teacher":
            if self.search([
                    ("teacher_id", "=", self.teacher_id.id),
                    ("id", "not in", self.ids),
                    ("state", "!=", "expire")]):
                raise UserError(_(
"""You cannot assign library card to same teacher more than once!"""))

    def running_state(self):
        """Change state to running"""
        # self.code = self.env["ir.sequence"].next_by_code("library.card"
        #         ) or _("New")
        self.code = f"LIB_{self.student_id.id_student}"   
                 
        self.state = "running"

    def draft_state(self):
        """Change state to draft"""
        self.state = "draft"

    def unlink(self):
        """Inherited method to check state at record deletion"""
        for rec in self:
            if rec.state == "running":
                raise UserError(_(
                    """You cannot delete a confirmed library card!"""))
        return super(LibraryCard, self).unlink()

    def librarycard_expire(self):
        """Schedular to change in librarycard state when end date is over"""
        current_date = fields.Datetime.today()
        library_card_obj = self.env["library.card"]
        for rec in library_card_obj.search(
                [("end_borrow", "<", current_date)]):
            rec.state = "expire"

    # #action view book issue
    # def action_view_book_issue(self):
    #     """Method to redirect at book issue"""
    #     return {
    #         'name': _("Book Issue"),
    #         'res_model': 'library.book.issue',
    #         'type': 'ir.actions.act_window',
    #         'context': {'create': False,'delete': False},
    #         'view_mode': 'tree',
    #         'domain': [("card_id", "=", self.id)],
    #     }



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
                match = re.search(r'Id Student: (\d+)', qr_data)
                if match:
                    qr_code_name = int(match.group(1))
                    print(f'ID Student QR Code: {qr_code_name}')

                    # qr_code = qr_code_number()  # Assume this function returns the scanned QR code

                    # Find the book with the scanned QR code
                    name_borrower = self.env['res.partner'].search([('id_student', '=', qr_code_name)])

                    # If book is found, fill the qbook_id field
                    if name_borrower:
                        self.student_id = name_borrower.id
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

    """ scan barcode of student """
    def action_scan_barcode_name_student(self, vals):
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
                    name_borrower = self.env['res.partner'].search([('id_student', '=', barcode_name)])

                    # If student is found, fill the student_id field
                    if name_borrower:
                        self.student_id = name_borrower.id
                        print(f'Student ID: {self.student_id}')
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

    def create_library_card_for_user(self, user_login):
        # Tìm người dùng dựa trên login
        user = self.env['res.users'].search([('login', '=', user_login)], limit=1)
        if not user:
            return False  # Người dùng không tìm thấy

        # Tạo bản ghi mới trong library.card
        library_card = self.env['library.card'].create({
            'user_id': user.id  # Gán ID người dùng
        })
        return library_card