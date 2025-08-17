# 🌱 SmallTree Academy - smalltree Management System

Hệ thống quản lý mầm non hiện đại với tích hợp AI, giúp quản lý chương trình học, thực đơn, điểm danh và nhiều chức năng khác.

## ✨ Tính năng chính

- **🤖 AI Dashboard**: Tạo chương trình học và thực đơn tự động bằng AI
- **📚 Quản lý chương trình học**: Tạo, chỉnh sửa và theo dõi chương trình học theo tuần
- **🍎 Quản lý thực đơn**: Lập thực đơn dinh dưỡng cho từng ngày trong tuần
- **✅ Điểm danh học sinh**: Hệ thống điểm danh với theo dõi tỷ lệ tham gia
- **👥 Quản lý tài khoản**: Phân quyền admin, teacher, parent
- **📱 Responsive Design**: Giao diện thân thiện trên mobile và desktop
- **📊 Báo cáo**: Xuất Excel, Word và các báo cáo quản lý

## 🚀 Cài đặt và chạy

### Yêu cầu hệ thống
- Python 3.8+
- Linux/Unix server
- Flask và các dependencies trong `requirements.txt`

### Cách 1: Development (Local)
```bash
# Clone repository
git clone https://github.com/athanhtuan11/smalltree.git
cd smalltree

# Tạo virtual environment
python3 -m venv venv
source venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt

# Chạy ứng dụng development
python run.py
```

### Cách 2: Production Deployment (Linux Server)
```bash
# Tự động setup với Nginx + Gunicorn
chmod +x setup_nginx_gunicorn.sh
./setup_nginx_gunicorn.sh
```

## 🔧 Cấu hình

### Database
- SQLite database sẽ được tạo tự động tại `app/site.db`
- Migrations được quản lý bằng Flask-Migrate

### AI Services
Cấu hình trong `multi_ai_config.py`:
- Cohere API (primary)
- Groq API (fast)
- Google Gemini (fallback)

### Environment Variables
Tạo file `.env` với:
```
SECRET_KEY=your-secret-key-here
COHERE_API_KEY=your-cohere-key
GROQ_API_KEY=your-groq-key  
GEMINI_API_KEY=your-gemini-key
```

## 📁 Cấu trúc project

```
smalltree-website/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── routes.py                # Routes và endpoints
│   ├── models.py                # Database models
│   ├── forms.py                 # WTForms
│   ├── multi_ai_service.py      # AI service integration
│   ├── enhanced_curriculum_ai.py # AI curriculum generation
│   ├── enhanced_menu_ai.py      # AI menu generation
│   ├── static/                  # CSS, JS, images
│   └── templates/               # Jinja2 templates
├── migrations/                  # Database migrations
├── .vscode/                     # VS Code configuration
├── config.py                    # App configuration
├── multi_ai_config.py           # AI services config
├── requirements.txt             # Python dependencies
├── run.py                       # Application entry point
└── README.md                    # Documentation
```

## 🎯 Sử dụng

### Đăng nhập
- **Admin**: Quản lý toàn bộ hệ thống
- **Teacher**: Quản lý chương trình học, thực đơn, điểm danh
- **Parent**: Xem thông tin con em

### AI Dashboard
1. Truy cập `/ai-dashboard`
2. Chọn tab "Chương trình học" hoặc "Thực đơn"
3. Nhập thông tin yêu cầu
4. AI sẽ tự động tạo nội dung phù hợp

### Mobile Support
- Giao diện responsive tối ưu cho mobile
- Touch-friendly buttons (44px minimum)
- Mobile-first CSS design

## 🚀 Production Deployment

### Lần đầu triển khai (Linux Server)

```bash
# Clone repository trên server
git clone https://github.com/athanhtuan11/smalltree.git
cd smalltree

# Chạy script tự động setup
chmod +x setup_nginx_gunicorn.sh
./setup_nginx_gunicorn.sh

# Script sẽ tự động:
# - Cài đặt Nginx, Gunicorn, Python dependencies
# - Tạo systemd service
# - Cấu hình Nginx reverse proxy
# - Setup SSL (Let's Encrypt) 
# - Tạo backup cron job
```

### Cập nhật code an toàn (Linux)

```bash
# Sử dụng maintenance script
chmod +x maintain_server.sh
./maintain_server.sh update
```

### Backup dữ liệu định kỳ

```bash
# Chạy backup thủ công
sudo /usr/local/bin/smalltree-backup.sh

# Hoặc sử dụng maintenance script
./maintain_server.sh backup
```

### Cấu hình số học sinh (cho tính toán khối lượng thực phẩm)

```bash
# Xem số học sinh hiện tại
python student_config.py

# Cập nhật số học sinh (ví dụ: 30 học sinh)
python student_config.py 30
```

### Quy trình 3 bước tự động tính khối lượng

Hệ thống sẽ tự động:
- ✅ Phân tích thực đơn và trích xuất nguyên liệu
- ✅ Tính toán khối lượng dựa trên số học sinh
- ✅ Ghép thông tin nhà cung cấp từ `/suppliers`
- ✅ Tạo 5 file Excel theo mẫu Bộ Y Tế với đầy đủ thông tin

**Khẩu phần tính toán:**
- Thịt: 50g/học sinh, Cá: 60g/học sinh
- Rau xanh: 80g/học sinh, Rau củ: 100g/học sinh  
- Gạo: 80g/học sinh, Sữa: 200ml/học sinh

### Cấu trúc data được bảo vệ
```
📁 Được GIT bỏ qua (an toàn):
├── app/site.db              # Database chính
├── app/static/uploads/      # File upload của user
├── app/static/images/activities/  # Ảnh hoạt động
├── .env.production          # Config production
├── backups/                 # Các file backup
└── logs/                    # Log files

📁 Được GIT quản lý (sẽ thay đổi):
├── app/*.py                 # Source code
├── app/templates/           # Templates
├── app/static/css/          # CSS files
└── requirements.txt         # Dependencies
```

## 🛠️ Development & Management

### Database Migrations
```bash
# Tạo migration mới
export FLASK_APP=run.py
flask db migrate -m "Description"

# Apply migrations
flask db upgrade
```

### Server Management (Production)
```bash
# Xem status services
./maintain_server.sh status

# Restart services
./maintain_server.sh restart

# Xem logs
./maintain_server.sh logs

# Health check
./maintain_server.sh health

# Update dependencies
./maintain_server.sh deps

# Clean system
./maintain_server.sh clean

# Install SSL certificate
./maintain_server.sh ssl
```

### Testing
```bash
# Test requirements
chmod +x test_requirements.sh
./test_requirements.sh

# Test Flask app
python -c "from app import create_app; app = create_app(); print('✅ App OK')"
```

## 📝 License

MIT License - xem file LICENSE để biết thêm chi tiết.

## 🤝 Contributing

1. Fork repository
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

## 📞 Hỗ trợ

Nếu có vấn đề, hãy tạo issue trên GitHub repository.

---

**SmallTree Academy** - *Ngôi nhà thứ hai của bé* 🌳

## 🌟 Quick Start Summary

### Development (Local)
```bash
git clone https://github.com/athanhtuan11/smalltree.git
cd smalltree && python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt && python run.py
```

### Production (Linux Server)
```bash
chmod +x setup_nginx_gunicorn.sh && ./setup_nginx_gunicorn.sh
```

### Management
```bash
./maintain_server.sh [update|restart|status|logs|backup|health|ssl]
```

---

*MIT License - See LICENSE file for details*
```

## Features

- **Home Page**: An overview of the smalltree and its mission.
- **About Page**: Information about the smalltree, its staff, and philosophy.
- **Classes Page**: Details about the different classes offered for children.
- **Gallery Page**: A collection of images showcasing activities and events at the smalltree.
- **Contact Page**: A form for parents to reach out with inquiries.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/smalltree-website.git
   cd smalltree-website
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Configure the application settings in `config.py` as needed.

## Running the Application

To run the application, execute the following command:
```
python run.py
```

The application will start on `http://127.0.0.1:5000/`.

## Contributing

Feel free to submit issues or pull requests if you have suggestions or improvements for the project.

## License

This project is licensed under the MIT License. See the LICENSE file for details.