# Hướng dẫn Deploy lên Server Ubuntu

## Vấn đề hiện tại
Server đang bị lỗi 502 Bad Gateway vì **bảng UserActivity chưa được tạo trong database**.

## Giải pháp: Chạy Migration trên Server

### Bước 1: SSH vào server
```bash
ssh user@your-server-ip
```

### Bước 2: Di chuyển vào thư mục project
```bash
cd /path/to/smalltree-website
```

### Bước 3: Kích hoạt virtual environment
```bash
source venv/bin/activate
# Hoặc
source env/bin/activate
```

### Bước 4: Pull code mới nhất từ GitHub
```bash
git pull origin master
```

### Bước 5: Cài đặt/nâng cấp dependencies
```bash
pip install -r requirements.txt --upgrade
```

### Bước 6: **QUAN TRỌNG** - Chạy migration để tạo bảng UserActivity
```bash
flask db upgrade
```

**Lệnh này sẽ tạo bảng `user_activity` trong database.**

### Bước 7: Restart Gunicorn service
```bash
sudo systemctl restart gunicorn
# Hoặc nếu dùng tên khác:
sudo systemctl restart smalltree
```

### Bước 8: Kiểm tra log để đảm bảo không có lỗi
```bash
sudo journalctl -u gunicorn -n 50 --no-pager
# Hoặc
sudo journalctl -u smalltree -n 50 --no-pager
```

### Bước 9: Kiểm tra status service
```bash
sudo systemctl status gunicorn
```

---

## Kiểm tra Database

### Kết nối vào PostgreSQL (nếu dùng PostgreSQL)
```bash
sudo -u postgres psql
\c smalltree_db
\dt
```

Bạn phải thấy bảng `user_activity` trong danh sách.

### Kiểm tra cấu trúc bảng
```sql
\d user_activity
```

### Kiểm tra có dữ liệu không
```sql
SELECT COUNT(*) FROM user_activity;
SELECT * FROM user_activity ORDER BY timestamp DESC LIMIT 10;
```

---

## Troubleshooting

### Lỗi: "Table 'user_activity' doesn't exist"
➡️ Chạy lại: `flask db upgrade`

### Lỗi: "No migrations to apply"
➡️ Kiểm tra file migration đã tồn tại chưa:
```bash
ls migrations/versions/
```

Phải có file: `e8af23953396_add_useractivity_table_for_tracking.py`

### Lỗi: Migration file không tồn tại trên server
➡️ Đảm bảo đã `git pull` đúng branch:
```bash
git status
git log --oneline -5
```

### Gunicorn không restart
```bash
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
```

### Kiểm tra Nginx log
```bash
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

---

## Sau khi Deploy thành công

1. Truy cập website: `http://your-domain.com/`
2. Đăng nhập admin: `http://your-domain.com/login`
3. Kiểm tra trang analytics: `http://your-domain.com/analytics`
4. Xem log hoạt động đã được ghi nhận

---

## Lưu ý quan trọng

- **Migration chỉ cần chạy 1 lần** khi lần đầu deploy tính năng mới
- Sau khi migration thành công, app sẽ tự động track mọi hoạt động
- Nếu bảng chưa tồn tại, app vẫn chạy bình thường (không crash) nhưng không ghi log
- Tính năng analytics chỉ hoạt động sau khi chạy migration thành công

---

## Checklist Deploy

- [ ] SSH vào server
- [ ] Activate virtualenv
- [ ] `git pull origin master`
- [ ] `pip install -r requirements.txt --upgrade`
- [ ] `flask db upgrade` ⬅️ **QUAN TRỌNG NHẤT**
- [ ] `sudo systemctl restart gunicorn`
- [ ] `sudo journalctl -u gunicorn -n 50` (check log)
- [ ] Test website hoạt động
- [ ] Test trang analytics: `/analytics`
- [ ] Kiểm tra database có bảng `user_activity`

---

## Liên hệ Support

Nếu gặp lỗi, gửi output của các lệnh sau:
```bash
flask db current
flask db heads
sudo journalctl -u gunicorn -n 100 --no-pager
sudo tail -100 /var/log/nginx/error.log
```
