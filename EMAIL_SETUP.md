# Hướng dẫn cấu hình Email cho Enrollment Notifications

## 📧 Cấu hình Gmail App Password

Để gửi email thông báo đăng ký khóa học, bạn cần:

### 1. Bật 2-Step Verification cho Gmail
- Truy cập: https://myaccount.google.com/security
- Tìm "2-Step Verification" và bật lên

### 2. Tạo App Password
- Truy cập: https://myaccount.google.com/apppasswords
- Chọn app: "Mail"
- Chọn device: "Other" → Nhập "SmallTree Website"
- Copy password được tạo (16 ký tự)

### 3. Cập nhật config.py hoặc .env
```python
# Option 1: Sửa trực tiếp trong config.py
MAIL_USERNAME = 'mamnoncaynho@gmail.com'
MAIL_PASSWORD = 'your-16-char-app-password-here'

# Option 2: Tạo file .env (khuyến nghị)
MAIL_USERNAME=mamnoncaynho@gmail.com
MAIL_PASSWORD=your-16-char-app-password-here
```

## ✅ Đã cài đặt
- ✅ Flask-Mail==0.9.1 đã được thêm vào requirements.txt
- ✅ Mail configuration đã được thêm vào config.py
- ✅ mail.init_app(app) đã được thêm vào __init__.py

## 🧪 Test Email
Sau khi cấu hình xong, test bằng cách:
1. Truy cập trang chi tiết khóa học
2. Click "Đăng ký học"
3. Điền form và gửi
4. Kiểm tra email mamnoncaynho@gmail.com

## ⚠️ Lưu ý
- **KHÔNG commit App Password lên Git!**
- Sử dụng file .env (đã có trong .gitignore)
- App Password khác với mật khẩu Gmail thường
- Nếu không cấu hình, hệ thống vẫn chạy nhưng không gửi được email

## 📝 Format email gửi đi
```
Subject: 🎓 Đăng ký khóa học mới: [Tên khóa học]

THÔNG BÁO ĐĂNG KÝ KHÓA HỌC MỚI
==================================================

Khóa học: [Tên khóa học]
Giá: [Giá tiền]đ

THÔNG TIN HỌC VIÊN:
- Họ và tên: [Tên học viên]
- Số điện thoại: [SĐT]
- Email: [Email]

GHI CHÚ:
[Ghi chú của học viên]

==================================================
Vui lòng liên hệ học viên trong 24h để xác nhận đăng ký.
```
