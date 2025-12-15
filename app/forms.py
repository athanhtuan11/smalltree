from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, PasswordField, SelectField, FloatField, IntegerField
from wtforms.validators import DataRequired, Email, Optional, EqualTo, Length, NumberRange
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import MultipleFileField

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send')

class EditProfileForm(FlaskForm):
    full_name = StringField('Họ tên', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Số điện thoại', validators=[DataRequired()])
    student_code = StringField('Mã số học sinh', validators=[Optional()])
    old_password = PasswordField('Mật khẩu cũ', validators=[Optional()])
    password = PasswordField('Mật khẩu mới', validators=[Optional()])
    confirm = PasswordField('Xác nhận mật khẩu mới', validators=[Optional(), EqualTo('password', message='Mật khẩu xác nhận không khớp')])
    submit = SubmitField('Lưu thay đổi')

class ActivityCreateForm(FlaskForm):
    title = StringField('Tiêu đề', validators=[DataRequired()])
    description = TextAreaField('Nội dung', validators=[DataRequired()])
    date = StringField('Ngày', validators=[DataRequired()])
    class_id = SelectField('Đăng cho lớp', coerce=int, validators=[Optional()])  # 0 = khách vãng lai
    background = FileField('Ảnh nền', validators=[Optional()])  # Bỏ FileAllowed - check manual trong route
    images = MultipleFileField('Ảnh hoạt động', validators=[Optional()])  # Bỏ FileAllowed - check manual trong route
    submit = SubmitField('Đăng bài')

class ActivityEditForm(FlaskForm):
    title = StringField('Tiêu đề', validators=[DataRequired()])
    description = TextAreaField('Nội dung', validators=[DataRequired()])
    class_id = SelectField('Đăng cho lớp', coerce=int, validators=[Optional()])
    background = FileField('Ảnh nền', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif','jfif'])])
    images = MultipleFileField('Ảnh hoạt động', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif','jfif'], 'Chỉ cho phép file ảnh!'), Optional()])
    submit = SubmitField('Lưu thay đổi')

class DeleteActivityForm(FlaskForm):
    pass

class SupplierForm(FlaskForm):
    name = StringField('Tên cơ sở', validators=[DataRequired(), Length(min=1, max=200)])
    address = TextAreaField('Địa chỉ', validators=[DataRequired(), Length(min=1, max=500)])
    phone = StringField('Số điện thoại', validators=[Length(max=20)])
    contact_person = StringField('Tên người liên hệ/giao hàng', validators=[Length(max=100)])
    supplier_type = SelectField('Loại nhà cung cấp', 
                               choices=[('fresh', 'Thực phẩm tươi sống'), ('dry', 'Thực phẩm khô')],
                               validators=[DataRequired()])
    registration_number = StringField('Số đăng ký kinh doanh', validators=[Length(max=100)])
    food_safety_cert = StringField('Giấy chứng nhận ATTP', validators=[Length(max=200)])
    submit = SubmitField('Lưu nhà cung cấp')

class ProductForm(FlaskForm):
    name = StringField('Tên sản phẩm', validators=[DataRequired(), Length(min=1, max=200)])
    category = SelectField('Loại sản phẩm', 
                          choices=[('fresh', 'Thực phẩm tươi sống'), ('dry', 'Thực phẩm khô')],
                          validators=[DataRequired()])
    supplier_id = SelectField('Nhà cung cấp', coerce=int, validators=[DataRequired()])
    unit = StringField('Đơn vị tính', validators=[DataRequired(), Length(min=1, max=20)])
    price = FloatField('Giá cả (VNĐ)', validators=[DataRequired(message='Giá sản phẩm là bắt buộc'), NumberRange(min=0, message='Giá phải lớn hơn 0')])
    submit = SubmitField('Lưu sản phẩm')