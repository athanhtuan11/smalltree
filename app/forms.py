from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, Optional, EqualTo
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

class ActivityForm(FlaskForm):
    title = StringField('Tiêu đề', validators=[DataRequired()])
    description = TextAreaField('Nội dung', validators=[DataRequired()])
    date = StringField('Ngày', validators=[DataRequired()])
    background = FileField('Ảnh nền', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif','jfif'])])
    images = MultipleFileField('Ảnh hoạt động', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif','jfif'], 'Chỉ cho phép file ảnh!'), Optional()])
    submit = SubmitField('Đăng bài')

class DeleteActivityForm(FlaskForm):
    pass