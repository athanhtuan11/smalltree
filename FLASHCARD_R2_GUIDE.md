# 📸 LƯU TRỮ ẢNH TRONG SMALLTREE - HƯỚNG DẪN TOÀN DIỆN

## 🗂️ TỔNG QUAN HỆ THỐNG LƯU TRỮ

SmallTree sử dụng **Cloudflare R2** để lưu trữ tất cả ảnh/audio với fallback về local VPS khi cần.

### 📊 Phân loại files

| Loại | Lưu trữ | Đường dẫn R2 | Ghi chú |
|------|---------|--------------|---------|
| **Flashcard - Deck covers** | R2 | `flashcard/covers/` | Ảnh bìa bộ thẻ |
| **Flashcard - Card images** | R2 | `flashcard/cards/` | Ảnh minh họa thẻ |
| **Flashcard - Audio** | R2 | `flashcard/audio/` | File âm thanh MP3/WAV |
| **Hoạt động (Activities)** | R2 | `activities/` | Ảnh hoạt động hàng ngày |
| **Album học sinh** | R2 | `student_albums/` | Ảnh album học sinh |
| **Avatar học sinh** | R2 | `students/avatars/` | Ảnh đại diện |

---

## 🔄 TRƯỚC VÀ SAU KHI CẬP NHẬT

### ❌ TRƯỚC (Code cũ)
```python
# Flashcard upload - CHỈ LOCAL
file.save(os.path.join(UPLOAD_FOLDER, 'images', filename))
cover_image = f"flashcard/images/{filename}"  # Path tương đối
```

**Vấn đề:**
- Ảnh lưu trên VPS (giới hạn dung lượng)
- Không có CDN (chậm với người dùng xa)
- Không scale được
- URL: `/static/flashcard/images/xxx.jpg`

### ✅ SAU (Code mới)
```python
# Flashcard upload - R2 với local fallback
if R2_ENABLED:
    r2_path = f"flashcard/cards/{filename}"
    r2.upload_file(file, r2_path)
    image_url = f"{r2.public_url}/{r2_path}"  # URL đầy đủ
else:
    # Fallback local nếu R2 lỗi
    file.save(local_path)
    image_url = f"flashcard/images/{filename}"
```

**Cải thiện:**
- ✅ Ảnh lưu trên R2 (không giới hạn)
- ✅ CDN toàn cầu (nhanh)
- ✅ Chi phí thấp (~$0.015/GB/tháng)
- ✅ URL: `https://pub-394238555e8a4caabd0328aee6913415.r2.dev/flashcard/cards/xxx.jpg`

---

## 🚀 HƯỚNG DẪN TRIỂN KHAI

### Bước 1: Cập nhật code trên VPS

```bash
# Trên máy local
git add .
git commit -m "Add R2 storage for flashcard module"
git push origin master

# Trên VPS
cd /var/www/smalltree-website
git pull origin master
source venv/bin/activate
```

### Bước 2: Kiểm tra R2 connection

```bash
# Test R2 credentials
python3 test_r2.py

# Nếu lỗi, kiểm tra .env
cat .env | grep R2_
```

### Bước 3: Migrate ảnh cũ lên R2 (NẾU CÓ)

```bash
# Chỉ chạy nếu đã có flashcard data local
python3 migrate_flashcard_to_r2.py
```

Script sẽ:
- Scan tất cả Deck và Card có ảnh local
- Upload lên R2
- Cập nhật database với URL mới
- Báo cáo kết quả

### Bước 4: Restart app

```bash
sudo supervisorctl restart smalltree
```

### Bước 5: Test upload mới

1. Đăng nhập admin
2. Vào `/flashcards/admin`
3. Tạo deck mới với cover image
4. Tạo card mới với image + audio
5. Kiểm tra console log:
   ```
   ✅ Uploaded cover to R2: https://pub-xxx.r2.dev/flashcard/covers/xxx.jpg
   ✅ Uploaded card image to R2: https://pub-xxx.r2.dev/flashcard/cards/xxx.jpg
   ✅ Uploaded audio to R2: https://pub-xxx.r2.dev/flashcard/audio/xxx.mp3
   ```

---

## 🗺️ CẤU TRÚC LƯU TRỮ

### Trên Cloudflare R2:

```
smalltree-images/  (bucket)
├── flashcard/
│   ├── covers/          # Deck cover images
│   │   └── 20251213120000_cover.jpg
│   ├── cards/           # Card images
│   │   ├── 20251213120100_apple.jpg
│   │   └── 20251213120200_banana.jpg
│   └── audio/           # Card audio files
│       ├── 20251213120100_apple.mp3
│       └── 20251213120200_banana.mp3
├── activities/          # Activity images
│   └── 20251213_outdoor.jpg
├── students/
│   └── avatars/         # Student avatars
│       └── student_123.jpg
└── student_albums/      # Student album photos
    └── album_456_photo1.jpg
```

### Trên VPS (Backup/Fallback):

```
app/static/
├── flashcard/
│   ├── images/          # Deck covers + Card images (fallback)
│   └── audio/           # Card audio (fallback)
├── images/
│   ├── activities/      # Activities (fallback)
│   ├── students/        # Student avatars (fallback)
│   └── flashcards/      # Old structure (deprecated)
└── student_albums/      # Student albums (fallback)
```

---

## 🔍 KIỂM TRA UPLOAD ĐANG LƯU Ở ĐÂU

### Cách 1: Xem console log

```bash
# Trên VPS
tail -f /var/www/smalltree-website/logs/gunicorn.out.log
```

Khi upload, sẽ thấy:
```
✅ Uploaded cover to R2: https://pub-xxx.r2.dev/flashcard/covers/xxx.jpg
```

hoặc

```
⚠️  R2 upload failed, saving local: [error]
```

### Cách 2: Kiểm tra database

```bash
cd /var/www/smalltree-website
source venv/bin/activate
flask shell
```

```python
from app.models import Deck, Card

# Kiểm tra Deck cover
deck = Deck.query.first()
print(deck.cover_image)
# R2: https://pub-xxx.r2.dev/flashcard/covers/xxx.jpg
# Local: flashcard/images/xxx.jpg

# Kiểm tra Card image
card = Card.query.first()
print(card.image_url)
# R2: https://pub-xxx.r2.dev/flashcard/cards/xxx.jpg
# Local: flashcard/images/xxx.jpg
```

### Cách 3: Inspect HTML source

F12 → Elements → Tìm `<img src="...">`:
- R2: `src="https://pub-394238555e8a4caabd0328aee6913415.r2.dev/..."`
- Local: `src="/static/flashcard/images/..."`

---

## 📊 SO SÁNH ACTIVITIES vs FLASHCARD

| Feature | Activities | Flashcard (CŨ) | Flashcard (MỚI) |
|---------|------------|----------------|-----------------|
| **Storage** | R2 | Local VPS | R2 + Local fallback |
| **Image path** | `activities/xxx.jpg` | `flashcard/images/xxx.jpg` | `flashcard/cards/xxx.jpg` |
| **URL format** | Full R2 URL | Relative path | Full R2 URL |
| **Batch upload** | ✅ 20 images/batch | ❌ Single | ❌ Single |
| **CDN** | ✅ Cloudflare | ❌ VPS only | ✅ Cloudflare |
| **Fallback** | ✅ Local | N/A | ✅ Local |

---

## 🛠️ TROUBLESHOOTING

### Vấn đề: Ảnh upload nhưng không hiển thị

**Nguyên nhân:** R2 bucket chưa public

**Giải pháp:**
1. Vào Cloudflare Dashboard
2. R2 → `smalltree-images`
3. Settings → Public Access → **Enable**
4. Copy Public URL: `https://pub-xxx.r2.dev`
5. Kiểm tra `.env`: `R2_PUBLIC_URL=https://pub-xxx.r2.dev`

### Vấn đề: Import error "No module named 'r2_storage'"

**Nguyên nhân:** File `r2_storage.py` không có hoặc sai vị trí

**Giải pháp:**
```bash
# Kiểm tra file tồn tại
ls /var/www/smalltree-website/r2_storage.py

# Nếu không có, copy từ local
scp r2_storage.py user@vps:/var/www/smalltree-website/
```

### Vấn đề: R2_ENABLED = False (app dùng local)

**Nguyên nhân:** Import r2_storage thất bại

**Giải pháp:**
```bash
# Kiểm tra import
python3 -c "from r2_storage import get_r2_storage; print('OK')"

# Nếu lỗi boto3
pip install boto3

# Nếu lỗi credentials
grep R2_ .env
```

### Vấn đề: Ảnh cũ (local) và ảnh mới (R2) trộn lẫn

**Nguyên nhân:** Chưa migrate ảnh cũ

**Giải pháp:**
```bash
# Migrate tất cả ảnh cũ lên R2
python3 migrate_flashcard_to_r2.py
```

---

## 💰 CHI PHÍ R2 CHO FLASHCARD

### Ước tính dữ liệu:

**Flashcard content:**
- 10 bộ thẻ (Decks) × 1 cover (500KB) = 5MB
- 200 thẻ (Cards) × 1 image (300KB) = 60MB
- 200 thẻ × 1 audio (50KB) = 10MB
- **Tổng: 75MB**

**Activities + Albums:**
- 1000 ảnh hoạt động × 500KB = 500MB
- 500 ảnh album × 500KB = 250MB
- **Tổng: 750MB**

**Grand Total: ~825MB (~0.8GB)**

### Chi phí Cloudflare R2:

- Storage: 0.8GB × $0.015 = **$0.012/tháng** (~300 VNĐ)
- Egress: **$0** (miễn phí không giới hạn)
- Operations: Negligible
- **Tổng: ~3,600 VNĐ/năm**

### So sánh với VPS storage:

- VPS 25GB SSD: $5-10/tháng (120k-240k VNĐ/năm)
- Khi đầy → Nâng cấp +$5/tháng
- **R2 rẻ hơn 30-60 lần**

---

## ✅ CHECKLIST HOÀN THÀNH

- [ ] Code đã update với R2 upload cho flashcard
- [ ] File `.env` có đầy đủ R2 credentials
- [ ] Module `r2_storage.py` tồn tại
- [ ] Đã test upload deck cover thành công
- [ ] Đã test upload card image thành công
- [ ] Đã test upload card audio thành công
- [ ] Console log hiển thị "✅ Uploaded to R2"
- [ ] Database lưu full R2 URL (https://pub-xxx.r2.dev/...)
- [ ] Ảnh hiển thị đúng trên frontend
- [ ] Đã migrate ảnh cũ (nếu có) lên R2
- [ ] Supervisor app đã restart

---

## 📞 HỖ TRỢ

Nếu gặp vấn đề:

1. **Xem logs:**
   ```bash
   tail -f /var/www/smalltree-website/logs/gunicorn.err.log
   ```

2. **Chạy diagnostic:**
   ```bash
   python3 check_vps_setup.py
   ```

3. **Test R2 connection:**
   ```bash
   python3 test_r2.py
   ```

4. **Kiểm tra database:**
   ```bash
   flask shell
   >>> from app.models import Deck, Card
   >>> Deck.query.first().cover_image
   >>> Card.query.first().image_url
   ```

---

**🎉 Hoàn thành! Tất cả ảnh flashcard giờ đã lưu trên Cloudflare R2!**

**URL mẫu:**
- Deck cover: `https://pub-394238555e8a4caabd0328aee6913415.r2.dev/flashcard/covers/20251213120000_abc.jpg`
- Card image: `https://pub-394238555e8a4caabd0328aee6913415.r2.dev/flashcard/cards/20251213120100_xyz.jpg`
- Card audio: `https://pub-394238555e8a4caabd0328aee6913415.r2.dev/flashcard/audio/20251213120100_xyz.mp3`
