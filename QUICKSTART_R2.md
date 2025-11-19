# HƯỚNG DẪN NHANH - CLOUDFLARE R2

## 🚀 SETUP TRONG 5 PHÚT

### 1. Tạo R2 Bucket trên Cloudflare
```
1. Vào: https://dash.cloudflare.com/
2. Click: R2 > Create bucket
3. Tên bucket: smalltree-images
4. Copy Account ID
```

### 2. Tạo API Token
```
1. R2 > Manage R2 API Tokens > Create API Token
2. Permissions: Object Read & Write
3. Copy Access Key + Secret Key (chỉ hiện 1 lần!)
```

### 3. Enable Public Access
```
1. Vào bucket smalltree-images
2. Settings > Public Access > Allow Access
3. Copy R2.dev URL: https://smalltree-images.<account-id>.r2.dev
```

### 4. Cấu hình App
Tạo file `.env` trong root project:
```bash
R2_ACCOUNT_ID=abc123def456
R2_ACCESS_KEY_ID=your-access-key
R2_SECRET_ACCESS_KEY=your-secret-key
R2_BUCKET_NAME=smalltree-images
R2_PUBLIC_URL=https://smalltree-images.abc123def456.r2.dev
```

### 5. Cài đặt
```bash
pip install boto3 pillow python-dotenv
```

### 6. Test
```bash
python -c "from r2_storage import get_r2_storage; r2 = get_r2_storage(); print('✅ OK' if r2.enabled else '❌ Failed')"
```

### 7. Migrate ảnh cũ (tùy chọn)
```bash
python migrate_to_r2.py
```

## ✅ XONG!

Bây giờ mỗi khi upload ảnh hoạt động:
- ✅ Tự động lên R2
- ✅ Tự động resize/optimize
- ✅ Phụ huynh tải MIỄN PHÍ băng thông
- ✅ Tiết kiệm dung lượng VPS

## 📊 CHI PHÍ

365GB/năm (1GB/ngày):
- Lưu trữ: 365GB x $0.015 = **$5.5/năm (~132,000đ/năm)**
- Download: **MIỄN PHÍ** ♾️
- **= ~11,000đ/tháng**

So sánh VPS 50GB: ~50,000đ/tháng → Tiết kiệm 80%!

## 🆘 CẦN GIÚP?

Đọc file: `R2_SETUP_GUIDE.md` (hướng dẫn chi tiết)
