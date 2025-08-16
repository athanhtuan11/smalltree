# Hướng dẫn tích hợp LLM Farm API

## Bước 1: Cấu hình API Key

### Cách 1: Sử dụng Environment Variables (Khuyến nghị)
Trong **Conda Prompt**, set environment variables:

```bash
# Mở Conda Prompt và chạy:
conda activate flaskenv
set LLM_FARM_API_KEY=your_actual_api_key_here
set LLM_FARM_BASE_URL=https://api.llmfarm.ai
set LLM_FARM_MODEL=gpt-3.5-turbo
```

### Cách 2: Chỉnh sửa config.py
Mở file `config.py` và thay đổi dòng:
```python
LLM_FARM_API_KEY = os.environ.get('LLM_FARM_API_KEY') or 'your_actual_api_key_here'
```

**Lưu ý**: 
- Thay `your_actual_api_key_here` bằng API key thực tế từ LLM Farm
- Kiểm tra tài liệu LLM Farm để có URL và model name chính xác

## Bước 2: Khởi động ứng dụng

**QUAN TRỌNG**: Phải sử dụng **Conda Prompt**, không phải PowerShell!

```bash
# 1. Mở Conda Prompt
# 2. Navigate to project folder
cd "D:\04_SmallTree\02_copilot_smalltree\nursery-website"

# 3. Activate environment
conda activate flaskenv

# 4. Run application  
python run.py
```

## Bước 4: Truy cập AI Dashboard

1. Mở trình duyệt và vào `http://localhost:5000`
2. Đăng nhập với tài khoản admin/teacher
3. Vào **Thực đơn** -> **AI Dashboard**

## Các tính năng AI có sẵn:

### 1. Gợi ý thực đơn AI
- Chọn độ tuổi trẻ em
- Nhập yêu cầu đặc biệt (dị ứng, chế độ ăn...)
- Số lượng gợi ý mong muốn
- AI sẽ tạo ra các món ăn phù hợp

### 2. Phân tích dinh dưỡng
- Nhập danh sách món ăn
- AI phân tích calo, protein, carb, chất béo
- Đánh giá tổng thể và gợi ý cải thiện

### 3. Gợi ý hoạt động giáo dục
- Chọn độ tuổi và loại hoạt động
- AI tạo ra các ý tưởng hoạt động phù hợp
- Các hoạt động an toàn và có tính giáo dục

### 4. Kiểm tra an toàn thực phẩm
- Nhập nguyên liệu và cách chế biến
- AI đánh giá mức độ an toàn
- Khuyến nghị bảo quản và chế biến

## API Endpoints (cho developers):

- `POST /ai/menu-suggestions` - Lấy gợi ý thực đơn
- `POST /ai/nutrition-analysis` - Phân tích dinh dưỡng
- `POST /ai/activity-suggestions` - Gợi ý hoạt động
- `POST /ai/food-safety-check` - Kiểm tra an toàn thực phẩm

## Xử lý lỗi:

Nếu API không hoạt động, hệ thống sẽ tự động sử dụng dữ liệu dự phòng để đảm bảo ứng dụng vẫn hoạt động bình thường.

## Bảo mật:

- API key được bảo vệ trong file `.env`
- Chỉ admin và teacher mới có quyền truy cập AI features
- Tất cả API calls đều được xác thực quyền trước khi thực hiện

## Tùy chỉnh:

Bạn có thể tùy chỉnh prompts và logic AI trong file `app/menu_ai.py` để phù hợp với nhu cầu cụ thể của trường mầm non.
