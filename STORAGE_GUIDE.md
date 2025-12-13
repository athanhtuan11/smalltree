# 🗄️ HƯỚNG DẪN LƯU TRỮ ẢNH CHO SMALLTREE

## 📊 So sánh các giải pháp lưu trữ

### 1. **Cloudflare R2** (✅ KHUYÊN DÙNG - BẠN ĐÃ CÓ)

**Ưu điểm:**
- ✅ **CHI PHÍ THẤP**: $0.015/GB/tháng (chỉ lưu trữ, không tính băng thông)
- ✅ **KHÔNG TỐN PHÍ DOWNLOAD**: 0đ cho egress bandwidth (khác S3)
- ✅ **NHANH**: CDN toàn cầu của Cloudflare
- ✅ **TƯƠNG THÍCH S3**: Dùng boto3 như AWS S3
- ✅ **PUBLIC URL**: Truy cập trực tiếp qua HTTP
- ✅ **AN TOÀN**: Backup tự động, không lo mất dữ liệu

**Nhược điểm:**
- ⚠️ Cần cấu hình đúng (đã có sẵn trong code của bạn)

**Chi phí ước tính:**
- 1000 ảnh (200MB trung bình): ~$0.003/tháng (~70 VNĐ)
- 10,000 ảnh (2GB): ~$0.03/tháng (~700 VNĐ)
- **KẾT LUẬN**: Gần như MIỄN PHÍ cho trường mầm non

---

### 2. **AWS S3** (💰 Đắt hơn R2)

**Ưu điểm:**
- Ổn định, phổ biến
- Nhiều tính năng nâng cao

**Nhược điểm:**
- ❌ **TỐN PHÍ DOWNLOAD**: $0.09/GB egress (đắt gấp 6 lần R2)
- ❌ **PHI THÚC**: $0.023/GB/tháng storage
- ❌ Cần thẻ tín dụng quốc tế

**Chi phí ước tính:**
- 2GB storage + 20GB download/tháng: ~$2-3/tháng (~70,000 VNĐ)

---

### 3. **Google Cloud Storage**

Tương tự S3, chi phí cao hơn R2.

---

### 4. **Local VPS Storage** (⚠️ KHÔNG KHUYÊN DÙNG)

**Ưu điểm:**
- Đơn giản, không cần config

**Nhược điểm:**
- ❌ **HẠN CHẾ DUNG LƯỢNG**: VPS thường có 20-50GB
- ❌ **KHÔNG SCALE**: Khi hết ổ cứng phải nâng cấp VPS (đắt)
- ❌ **CHẬM**: Không có CDN
- ❌ **RỦI RO MẤT DỮ LIỆU**: Nếu VPS die thì mất hết ảnh
- ❌ **TĂNG TẢI SERVER**: Download ảnh làm chậm app

---

### 5. **BackBlaze B2**

- Chi phí: $0.005/GB/tháng (rẻ hơn R2)
- Egress: $0.01/GB (có miễn phí 1GB/ngày)
- Nhược điểm: Chậm hơn Cloudflare, ít phổ biến hơn

---

## 🎯 KHUYẾN NGHỊ CHO SMALLTREE

### ✅ **SỬ DỤNG CLOUDFLARE R2** (Giải pháp tốt nhất)

**Lý do:**
1. **Chi phí thấp nhất**: Gần như miễn phí cho 10-20GB ảnh
2. **Nhanh**: CDN Cloudflare có server tại Việt Nam
3. **Không giới hạn download**: Phụ huynh xem ảnh không tốn phí
4. **Đã tích hợp sẵn**: Code của bạn đã có `r2_storage.py`

### 📝 CẤU HÌNH R2 TRÊN VPS

Bạn đã có cấu hình trong `.env`, chỉ cần đảm bảo:

```bash
# 1. Copy .env lên VPS
scp .env user@your-vps:/var/www/smalltree-website/

# 2. Kiểm tra module r2_storage.py có trên VPS
ls /var/www/smalltree-website/r2_storage.py

# 3. Cài đặt boto3
pip install boto3

# 4. Test kết nối R2
python3 test_r2.py
```

### 🔧 CẤU HÌNH HYBRID (R2 + LOCAL FALLBACK)

Code hiện tại của bạn đã có fallback:
```python
if R2_ENABLED:
    # Upload lên R2
    r2.upload_file(...)
else:
    # Lưu local nếu R2 lỗi
    file.save(local_path)
```

**Strategy:**
1. **Ảnh hoạt động, flashcard**: Lưu R2 (truy cập nhiều, cần CDN)
2. **Ảnh tạm, cache**: Lưu local VPS
3. **Backup**: Định kỳ sync R2 → Google Drive (dùng rclone)

---

## 🚀 SETUP R2 CHO VPS (HƯỚNG DẪN CHI TIẾT)

### Bước 1: Upload code lên VPS

```bash
# Trên máy local
git add .
git commit -m "Add VPS deployment scripts"
git push origin master

# Trên VPS
cd /var/www/smalltree-website
git pull origin master
```

### Bước 2: Chạy script kiểm tra

```bash
# Trên VPS
cd /var/www/smalltree-website
python3 check_vps_setup.py
```

Nếu thấy lỗi ❌ thì fix theo hướng dẫn.

### Bước 3: Deploy production

```bash
# Trên VPS
chmod +x deploy_vps.sh
sudo ./deploy_vps.sh
```

### Bước 4: Kiểm tra app

```bash
# Xem logs
tail -f /var/www/smalltree-website/logs/gunicorn.err.log

# Check status
sudo supervisorctl status smalltree

# Test URL
curl http://localhost:8000
```

### Bước 5: Fix lỗi Internal Server Error

Nếu vẫn lỗi khi vào `/flashcard/admin`:

```bash
# 1. Xem log chi tiết
tail -f /var/www/smalltree-website/logs/gunicorn.err.log

# 2. Kiểm tra database
cd /var/www/smalltree-website
source venv/bin/activate
flask shell

>>> from app.models import Deck, Card
>>> Deck.query.count()
>>> Card.query.count()

# 3. Nếu thiếu table, chạy migrations
flask db upgrade

# 4. Restart app
sudo supervisorctl restart smalltree
```

---

## 💰 CHI PHÍ ƯỚC TÍNH

### Scenario: Trường mầm non 100 học sinh

**Dữ liệu ước tính:**
- 100 học sinh × 50 ảnh/năm = 5,000 ảnh
- Mỗi ảnh ~500KB (đã optimize)
- Tổng: 2.5GB/năm

**Chi phí Cloudflare R2:**
- Storage: 2.5GB × $0.015 = **$0.0375/tháng** (~900 VNĐ)
- Egress: **$0** (miễn phí)
- **Tổng: ~11,000 VNĐ/năm**

**So sánh VPS storage:**
- VPS 1GB RAM + 25GB SSD: $5-10/tháng (120,000-240,000 VNĐ/năm)
- Hết dung lượng → Phải nâng cấp VPS (thêm $5-10/tháng)

**KẾT LUẬN**: R2 rẻ hơn 10-20 lần!

---

## 📋 CHECKLIST TRƯỚC KHI PRODUCTION

- [ ] File `.env` có đầy đủ R2 credentials
- [ ] Module `r2_storage.py` tồn tại
- [ ] Package `boto3` đã cài đặt
- [ ] Test upload ảnh thành công (`python3 test_r2.py`)
- [ ] Database đã migrate (`flask db upgrade`)
- [ ] Nginx client_max_body_size = 200M
- [ ] Supervisor đang chạy app
- [ ] Logs không có lỗi critical

---

## 🆘 TROUBLESHOOTING

### Lỗi: "No module named 'boto3'"
```bash
pip install boto3
sudo supervisorctl restart smalltree
```

### Lỗi: "Access Denied" khi upload R2
```bash
# Kiểm tra credentials trong .env
grep R2_ .env

# Test credentials
python3 -c "from r2_storage import get_r2_storage; r2 = get_r2_storage(); print(r2.bucket_name)"
```

### Lỗi: Internal Server Error trang admin
```bash
# Xem lỗi cụ thể
tail -f logs/gunicorn.err.log

# Thường là do:
# 1. Database chưa migrate → flask db upgrade
# 2. Session/login chưa đúng → Đăng nhập lại
# 3. Import module lỗi → Kiểm tra requirements.txt
```

### Ảnh upload nhưng không hiển thị
```bash
# Kiểm tra R2 public URL
curl https://pub-394238555e8a4caabd0328aee6913415.r2.dev/flashcard/test.jpg

# Nếu 403 → Bucket chưa public
# Vào Cloudflare dashboard → R2 → Settings → Public Access → Enable
```

---

## 📞 LIÊN HỆ HỖ TRỢ

Nếu cần hỗ trợ thêm:
1. Chạy `python3 check_vps_setup.py` và gửi kết quả
2. Copy nội dung `logs/gunicorn.err.log` (50 dòng cuối)
3. Chạy `sudo supervisorctl status` và gửi output

---

**🎉 Chúc bạn deploy thành công!**
