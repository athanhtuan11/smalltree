# Chức năng Ẩn/Hiện Học sinh (Soft Delete)

## Tóm tắt
Đã thêm chức năng ẩn học sinh thay vì xóa hoàn toàn, tương tự như chức năng ẩn món ăn. Dữ liệu học sinh vẫn được lưu giữ trong database nhưng sẽ không hiển thị trong các danh sách chính.

## Thay đổi chính

### 1. Model Database
- **File**: `app/models.py`
- **Thay đổi**: Thêm trường `is_active = db.Column(db.Boolean, default=True)` vào model `Child`
- **Migration**: Đã tạo và áp dụng migration `0cf69c6ce50f_add_is_active_field_to_child_model.py`

### 2. Route Cập nhật
- **File**: `app/routes.py`
- **Thay đổi chính**:
  - `student_list()`: Thêm tùy chọn hiển thị tất cả hoặc chỉ học sinh đang học
  - `toggle_student_status()`: Route mới để ẩn/hiện học sinh
  - Cập nhật tất cả query `Child.query.all()` thành `Child.query.filter_by(is_active=True).all()` trong:
    - Điểm danh (`attendance`, `mark_attendance`)
    - Lịch sử điểm danh (`attendance_history`)
    - Quản lý tài khoản (`accounts`)
    - Xuất file Excel và Word (`export_students`, `export_subsidized`)

### 3. Template Cập nhật
- **File**: `app/templates/student_list.html`
- **Thay đổi**:
  - Thêm CSS `.student-inactive` để làm mờ học sinh đã nghỉ
  - Thêm nút "Chỉ xem đang học" / "Xem tất cả"
  - Cập nhật cột thao tác:
    - Nút ẩn/hiện (màu xám/xanh với icon mắt)
    - Nút xóa vĩnh viễn (màu đỏ)
    - Badge "Đã nghỉ" cho học sinh bị ẩn
  - Tối ưu hiển thị: chỉ hiển thị icon cho nút, tooltip để giải thích

## Chức năng mới

### 1. Ẩn/Hiện học sinh
- **URL**: `POST /students/<id>/toggle`
- **Quyền**: Admin, Teacher
- **Chức năng**: Chuyển đổi trạng thái `is_active` của học sinh

### 2. Xem tất cả học sinh
- **URL**: `GET /students?show_all=true`
- **Quyền**: Admin, Teacher
- **Chức năng**: Hiển thị cả học sinh đang học và đã nghỉ

### 3. Hiển thị trạng thái
- Học sinh đã nghỉ sẽ có:
  - Badge màu vàng "Đã nghỉ"
  - Background màu xám nhạt
  - Opacity giảm

## Lợi ích
1. **Bảo toàn dữ liệu**: Không mất thông tin học sinh và lịch sử học tập
2. **Giao diện sạch**: Danh sách chính chỉ hiển thị học sinh đang học
3. **Linh hoạt**: Có thể dễ dàng khôi phục học sinh khi cần
4. **Nhất quán**: Tương tự chức năng ẩn món ăn đã có

## Tương thích ngược
- Tất cả học sinh hiện tại sẽ có `is_active = True` mặc định
- Các chức năng cũ vẫn hoạt động bình thường
- Không ảnh hưởng đến dữ liệu đã có

## Hướng dẫn sử dụng
1. Vào **Danh sách học sinh**
2. Nhấn nút **mắt xám** để ẩn học sinh
3. Nhấn **"Xem tất cả"** để thấy cả học sinh đã nghỉ
4. Nhấn nút **mắt xanh** để hiện lại học sinh
5. Nút **thùng rác đỏ** để xóa vĩnh viễn (cần cẩn thận!)