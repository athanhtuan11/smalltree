# Fix Lỗi SQLAlchemy trên Server Production

## Lỗi gặp phải
```
AttributeError: module 'sqlalchemy' has no attribute '__all__'
```

## Nguyên nhân
Flask-SQLAlchemy 2.5.1 không tương thích với SQLAlchemy 2.x

## Giải pháp

### Cách 1: Upgrade Flask-SQLAlchemy (Khuyến nghị)
```bash
# SSH vào server
cd /path/to/your/project

# Activate virtual environment
source venv/bin/activate  # hoặc conda activate your_env

# Upgrade Flask-SQLAlchemy
pip install Flask-SQLAlchemy==3.0.5

# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

### Cách 2: Pin SQLAlchemy version cũ
```bash
# SSH vào server
cd /path/to/your/project
source venv/bin/activate

# Install SQLAlchemy 1.4.x
pip install SQLAlchemy==1.4.46

# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

### Cách 3: Cập nhật requirements.txt (Tốt nhất)
Thay đổi trong `requirements.txt`:

```
# Thay đổi từ:
Flask-SQLAlchemy==2.5.1

# Thành:
Flask-SQLAlchemy==3.0.5
SQLAlchemy==2.0.23
```

Sau đó trên server:
```bash
pip install -r requirements.txt --upgrade
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

## Kiểm tra sau khi fix
```bash
# Test import
python -c "from app import create_app; app = create_app(); print('OK')"

# Kiểm tra service
sudo systemctl status gunicorn
sudo systemctl status nginx

# Xem log nếu còn lỗi
sudo tail -f /var/log/nginx/error.log
sudo journalctl -u gunicorn -f
```

## Lưu ý về Migration
Sau khi upgrade Flask-SQLAlchemy, có thể cần chạy lại migration:

```bash
flask db upgrade
```

## Nếu vẫn lỗi
1. Xóa cache Python: `find . -type d -name __pycache__ -exec rm -r {} +`
2. Reinstall tất cả packages: `pip install -r requirements.txt --force-reinstall`
3. Check Python version: `python --version` (cần >= 3.7)
