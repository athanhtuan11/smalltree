# 🌱 SmallTree Academy - Nursery Management System

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
- Python 3.7+
- Flask và các dependencies trong `requirements.txt`

### Cách 1: Chạy nhanh
```bash
# Double-click file quick_start.bat
# Hoặc chạy từ terminal:
quick_start.bat
```

### Cách 2: Cài đặt thủ công
```bash
# Clone repository
git clone <repository-url>
cd nursery-website

# Cài đặt dependencies
pip install -r requirements.txt

# Chạy ứng dụng
python run.py
```

### Cách 3: Sử dụng VS Code
1. Mở project trong VS Code
2. Nhấn `Ctrl+Shift+P` → "Tasks: Run Task" → "Run Flask App"

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
nursery-website/
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

## 🛠️ Development

### Database Migrations
```bash
# Tạo migration mới
flask db migrate -m "Description"

# Apply migrations
flask db upgrade
```

### Testing
```bash
# Chạy tests (nếu có)
python -m pytest
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
│       ├── index.html
│       ├── about.html
│       ├── classes.html
│       ├── gallery.html
│       └── contact.html
├── config.py
├── requirements.txt
├── run.py
└── README.md
```

## Features

- **Home Page**: An overview of the nursery and its mission.
- **About Page**: Information about the nursery, its staff, and philosophy.
- **Classes Page**: Details about the different classes offered for children.
- **Gallery Page**: A collection of images showcasing activities and events at the nursery.
- **Contact Page**: A form for parents to reach out with inquiries.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/nursery-website.git
   cd nursery-website
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