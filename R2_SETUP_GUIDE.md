# HƯỚNG DẪN SETUP CLOUDFLARE R2

## 📋 TỔNG QUAN
Cloudflare R2 là dịch vụ lưu trữ object storage tương thích S3, **miễn phí băng thông** (egress).

**Chi phí:**
- 💾 Lưu trữ: $0.015/GB/tháng (~360đ/GB)
- 📥 Download: **MIỄN PHÍ**
- 📤 Upload: **MIỄN PHÍ**
- 100GB = ~36,000đ/tháng

## 🚀 BƯỚC 1: TẠO CLOUDFLARE R2

### 1.1. Đăng ký/Đăng nhập Cloudflare
- Truy cập: https://dash.cloudflare.com
- Đăng ký tài khoản miễn phí (nếu chưa có)

### 1.2. Kích hoạt R2
1. Vào Dashboard > **R2**
2. Click **Purchase R2 Plan** (miễn phí, chỉ tính theo usage)
3. Xác nhận thanh toán (cần thêm thẻ, nhưng sẽ không charge nếu dùng ít)

### 1.3. Tạo Bucket
1. Click **Create bucket**
2. Điền:
   - **Bucket name**: `smalltree-images` (hoặc tên khác)
   - **Location**: Auto (Cloudflare tự chọn gần nhất)
3. Click **Create bucket**

### 1.4. Lấy Account ID
- Ở R2 Dashboard, copy **Account ID** (dạng: `abc123def456...`)

## 🔑 BƯỚC 2: TẠO API TOKEN

### 2.1. Tạo API Token
1. Vào R2 Dashboard > **Manage R2 API Tokens**
2. Click **Create API Token**
3. Cấu hình:
   - **Token name**: `smalltree-app`
   - **Permissions**: 
     - ✅ Object Read & Write
     - ✅ Object Delete (nếu cần xóa)
   - **Bucket**: `smalltree-images` (hoặc All buckets)
   - **TTL**: Forever
4. Click **Create API Token**

### 2.2. Lưu thông tin
Sao chép 2 thông tin (CHỈ HIỆN 1 LẦN):
- ✅ **Access Key ID**: `abc123...`
- ✅ **Secret Access Key**: `xyz789...`

⚠️ **LƯU Ý**: Secret key chỉ hiện 1 lần, lưu cẩn thận!

## 🌐 BƯỚC 3: SETUP PUBLIC ACCESS

### Option 1: Dùng R2.dev (MIỄN PHÍ, NHANH)

1. Vào bucket `smalltree-images`
2. Tab **Settings** > **Public Access**
3. Click **Allow Access**
4. Copy **R2.dev subdomain**: `https://smalltree-images.<account-id>.r2.dev`

✅ **Khuyến nghị**: Dùng R2.dev vì:
- Miễn phí
- HTTPS tự động
- CDN toàn cầu
- Không cần cấu hình thêm

### Option 2: Custom Domain (TÙY CHỌN)

Nếu muốn dùng domain riêng (vd: `cdn.smalltree.vn`):

1. Domain phải dùng Cloudflare DNS
2. Vào bucket > **Settings** > **Custom Domains**
3. Click **Connect Domain**
4. Chọn domain: `cdn.smalltree.vn`
5. Cloudflare tự động setup DNS

## ⚙️ BƯỚC 4: CẤU HÌNH APP

### 4.1. Cài đặt thư viện
```bash
pip install boto3 pillow
```

### 4.2. Cấu hình môi trường

**Option A: Dùng file .env (KHUYẾN NGHỊ)**

Tạo file `.env` trong root project:
```bash
# Cloudflare R2 Configuration
R2_ACCOUNT_ID=your-account-id-here
R2_ACCESS_KEY_ID=your-access-key-id-here
R2_SECRET_ACCESS_KEY=your-secret-access-key-here
R2_BUCKET_NAME=smalltree-images
R2_PUBLIC_URL=https://smalltree-images.your-account-id.r2.dev
```

**Option B: Sửa trực tiếp config_r2.py**

```python
R2_CONFIG = {
    'account_id': 'abc123def456',  # Thay bằng Account ID thật
    'access_key_id': 'xyz789...',   # Thay bằng Access Key thật
    'secret_access_key': 'secret123...', # Thay bằng Secret Key thật
    'bucket_name': 'smalltree-images',
    'public_url': 'https://smalltree-images.abc123def456.r2.dev',
}
```

### 4.3. Test kết nối
```bash
python -c "from r2_storage import get_r2_storage; r2 = get_r2_storage(); print('✅ R2 OK' if r2.enabled else '❌ R2 Failed')"
```

## 🔄 BƯỚC 5: MIGRATE ẢNH CŨ

### 5.1. Chạy migration thủ công
```bash
# Test migrate 10 ảnh đầu tiên
python migrate_to_r2.py

# Kiểm tra kết quả trên R2 Dashboard
```

### 5.2. Setup cronjob (tự động migrate)
```bash
# Mở crontab
crontab -e

# Thêm job chạy mỗi giờ
0 * * * * cd /path/to/smalltree-website && /path/to/venv/bin/python migrate_to_r2.py >> logs/r2-migration.log 2>&1

# Hoặc chạy mỗi ngày 3h sáng
0 3 * * * cd /path/to/smalltree-website && /path/to/venv/bin/python migrate_to_r2.py >> logs/r2-migration.log 2>&1
```

### 5.3. Kiểm tra log migration
```bash
tail -f logs/r2-migration.log
```

## 📊 BƯỚC 6: GIÁM SÁT

### 6.1. Kiểm tra dung lượng R2
```python
python -c "from r2_storage import get_r2_storage; r2 = get_r2_storage(); print(r2.get_storage_stats())"
```

### 6.2. Cloudflare Dashboard
- Vào R2 > Bucket > **Metrics**
- Xem:
  - Storage used (GB)
  - Operations (requests)
  - Egress (downloads)

### 6.3. Chi phí ước tính
```
100GB x $0.015 = $1.5/tháng (~36,000đ)
Download: MIỄN PHÍ ♾️
```

## 🔧 TÙY CHỈNH

### Thay đổi cấu hình upload

File `config_r2.py`:

```python
UPLOAD_CONFIG = {
    'max_file_size': 10,        # MB
    'resize_before_upload': True,
    'max_width': 1920,           # pixel
    'max_height': 1080,
    'quality': 85,               # JPEG quality (1-100)
    'delete_local_after_upload': True,  # Xóa local sau upload
    'keep_local_days': 7,        # Giữ backup local 7 ngày
}
```

### Migration config

```python
MIGRATION_CONFIG = {
    'auto_migrate_old_images': True,
    'min_age_days': 1,           # Chỉ migrate ảnh cũ hơn 1 ngày
    'batch_size': 50,            # Số ảnh migrate mỗi lần
}
```

## 🆘 XỬ LÝ LỖI

### Lỗi: "R2 chưa được cấu hình"
```bash
# Kiểm tra .env
cat .env | grep R2_

# Hoặc kiểm tra config_r2.py
python -c "from config_r2 import is_r2_configured; print(is_r2_configured())"
```

### Lỗi: "Access Denied"
- Kiểm tra API Token còn hiệu lực
- Kiểm tra quyền của token (Object Read & Write)
- Tạo token mới nếu cần

### Lỗi: "Bucket not found"
- Kiểm tra tên bucket đúng chưa
- Kiểm tra Account ID đúng chưa

### Ảnh không hiển thị
```bash
# Test URL trực tiếp
curl https://smalltree-images.your-account-id.r2.dev/activities/test.jpg

# Kiểm tra Public Access của bucket
# R2 Dashboard > Bucket > Settings > Public Access = Allowed
```

## 📈 HIỆU SUẤT

### Upload speed
- **VPS Upload**: ~5-20 MB/s (phụ thuộc VPS)
- **Local → R2**: ~10-50 MB/s

### Download speed
- **R2 + CDN**: 50-200 MB/s (phụ thuộc vị trí người dùng)
- **Latency**: <100ms (Cloudflare có 200+ datacenters)

### So sánh
| | Local VPS | R2 + CDN |
|---|-----------|----------|
| Tốc độ download | 10-50 MB/s | 50-200 MB/s |
| Băng thông | Tính tiền | **MIỄN PHÍ** |
| CDN | Không | Có (275+ cities) |
| Dung lượng | Giới hạn | ~Unlimited |

## ✅ CHECKLIST

- [ ] Tạo Cloudflare account
- [ ] Kích hoạt R2
- [ ] Tạo bucket `smalltree-images`
- [ ] Lấy Account ID
- [ ] Tạo API Token (Access Key + Secret Key)
- [ ] Enable Public Access (R2.dev)
- [ ] Cài `boto3` và `pillow`
- [ ] Cấu hình `.env` hoặc `config_r2.py`
- [ ] Test kết nối R2
- [ ] Chạy migrate thử
- [ ] Setup cronjob migration
- [ ] Giám sát dung lượng

## 🎓 BEST PRACTICES

1. **Luôn dùng .env** cho production (bảo mật)
2. **Enable Public Access** để phụ huynh xem ảnh
3. **Resize ảnh** trước khi upload (tiết kiệm storage)
4. **Migrate dần dần** (batch_size=50, chạy định kỳ)
5. **Backup local 7 ngày** trước khi xóa (an toàn)
6. **Monitor chi phí** qua Cloudflare Dashboard
7. **Dùng R2.dev domain** (miễn phí, nhanh, HTTPS)

## 📞 HỖ TRỢ

Nếu gặp lỗi:
1. Kiểm tra `.env` hoặc `config_r2.py`
2. Chạy: `python migrate_to_r2.py` và gửi log
3. Kiểm tra R2 Dashboard > Metrics
4. Xem log: `tail -f logs/r2-migration.log`
