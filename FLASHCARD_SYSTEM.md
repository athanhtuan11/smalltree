# 📚 HỆ THỐNG FLASHCARD CHO TRẺ MẦM NON

## ✨ Tính năng

### 🎯 Cho học sinh/trẻ em:
- **3 chế độ học tương tác:**
  - 🎴 **Flash Mode**: Xem thẻ, nghe phát âm tiếng Việt (TTS)
  - ❓ **Quiz Mode**: Trắc nghiệm 3 đáp án với pháo hoa khi đúng
  - 🎧 **Audio Mode**: Nghe âm thanh và chọn hình đúng

- **Giao diện thân thiện trẻ em:**
  - Màu pastel nhẹ nhàng (mint, pink, yellow, blue, purple)
  - Icon và emoji sinh động
  - Animation mượt mà với Anime.js
  - Responsive, tương thích điện thoại và tablet

- **Gamification:**
  - ⭐ Tích sao mỗi thẻ học (10 sao/thẻ)
  - 🔥 Streak theo ngày học liên tục
  - 🎁 Sticker khi hoàn thành bộ thẻ
  - 🎉 Pháo hoa khi trả lời đúng

- **Spaced Repetition (thuật toán Anki):**
  - Tự động tính khoảng cách ôn tập
  - Theo dõi độ khó (Hard/Good/Easy)
  - Lưu tiến độ học cho từng trẻ

### 👩‍🏫 Cho giáo viên/admin:
- **Quản lý bộ thẻ:**
  - Tạo bộ thẻ theo độ tuổi (1-3, 3-5, 5-7 tuổi)
  - Upload hình bìa đẹp mắt
  - Bật/tắt hiển thị bộ thẻ

- **Quản lý thẻ:**
  - Thêm thẻ với hình ảnh + text
  - Upload audio tùy chỉnh (giọng cô giáo)
  - Preview hình ảnh và audio trước khi lưu

- **Theo dõi tiến độ:**
  - Xem thống kê học của từng trẻ
  - Số thẻ đã học, điểm số, streak

---

## 🚀 CÀI ĐẶT

### 1. Tạo migration cho database

```bash
# Di chuyển vào thư mục dự án
cd d:\04_SmallTree\02_copilot_smalltree\smalltree-website

# Tạo migration mới
flask db migrate -m "add Flashcard models (Deck, Card, CardProgress, DeckProgress)"

# Áp dụng migration
flask db upgrade
```

### 2. Tạo thư mục cho upload files

```bash
mkdir app\static\flashcard\images
mkdir app\static\flashcard\audio
```

### 3. Khởi động server Flask

```bash
python run.py
```

---

## 📁 CẤU TRÚC THƯ MỤC

```
smalltree-website/
├── app/
│   ├── flashcard/
│   │   ├── __init__.py          # Blueprint routes (Flash/Quiz/Audio/Admin)
│   │   └── templates/
│   │       └── flashcard/
│   │           ├── base.html              # Base template
│   │           ├── index.html             # Trang chủ - chọn độ tuổi
│   │           ├── deck_list.html         # Danh sách bộ thẻ
│   │           ├── deck_detail.html       # Chi tiết bộ - chọn chế độ
│   │           ├── learn_flash.html       # Flash Mode
│   │           ├── learn_quiz.html        # Quiz Mode
│   │           ├── learn_audio.html       # Audio Mode
│   │           ├── rewards.html           # Màn hình phần thưởng
│   │           ├── admin.html             # Quản lý flashcard
│   │           ├── create_deck.html       # Tạo bộ thẻ
│   │           ├── edit_deck.html         # Sửa bộ thẻ
│   │           ├── manage_cards.html      # Quản lý thẻ
│   │           └── create_card.html       # Tạo thẻ mới
│   ├── static/
│   │   └── flashcard/
│   │       ├── flashcard.css      # CSS giao diện pastel
│   │       ├── flashcard.js       # JavaScript (Howler.js + Anime.js)
│   │       ├── images/            # Upload hình ảnh
│   │       └── audio/             # Upload audio
│   └── models.py                  # Thêm Deck, Card, CardProgress, DeckProgress
```

---

## 🎨 CÔNG NGHỆ SỬ DỤNG

### Backend:
- **Flask** - Web framework
- **SQLAlchemy** - ORM database
- **Flask-Migrate** - Database migrations
- **Werkzeug** - File upload security

### Frontend:
- **HTML5 + CSS3** - Markup và styling
- **JavaScript ES6** - Logic tương tác
- **Bootstrap 5** - Layout và responsive
- **Google Fonts (Nunito)** - Font thân thiện trẻ em

### Libraries:
- **Howler.js** - Phát audio (fallback to Web Speech API TTS)
- **Anime.js** - Animation mượt mà
- **Web Speech API** - Text-to-Speech tiếng Việt

---

## 🌐 ROUTES (URL)

### 👶 Cho học sinh:
- `/flashcards/` - Trang chủ (chọn độ tuổi)
- `/flashcards/age/<age_group>` - Danh sách bộ thẻ (1-3, 3-5, 5-7)
- `/flashcards/deck/<deck_id>` - Chi tiết bộ (chọn chế độ học)
- `/flashcards/learn/<deck_id>` - Flash Mode
- `/flashcards/quiz/<deck_id>` - Quiz Mode
- `/flashcards/audio/<deck_id>` - Audio Mode
- `/flashcards/rewards` - Màn hình phần thưởng

### 👩‍🏫 Cho giáo viên/admin:
- `/flashcards/admin` - Quản lý tất cả bộ thẻ
- `/flashcards/admin/deck/create` - Tạo bộ thẻ mới
- `/flashcards/admin/deck/<deck_id>/edit` - Sửa bộ thẻ
- `/flashcards/admin/deck/<deck_id>/cards` - Quản lý thẻ trong bộ
- `/flashcards/admin/deck/<deck_id>/card/create` - Tạo thẻ mới
- `/flashcards/admin/card/<card_id>/delete` - Xóa thẻ

### 🔌 API Endpoints:
- `POST /flashcards/api/update-progress` - Cập nhật tiến độ từng thẻ
- `POST /flashcards/api/update-deck-progress` - Cập nhật tiến độ bộ thẻ

---

## 📊 DATABASE MODELS

### 1. Deck (Bộ thẻ)
```python
- id: Integer (Primary Key)
- title: String(100) - "Con vật", "Màu sắc"
- description: String(500) - Mô tả bộ thẻ
- age_group: String(10) - "1-3", "3-5", "5-7"
- cover_image: String(300) - Đường dẫn hình bìa
- created_by: Integer (ForeignKey Staff.id)
- created_at: DateTime
- is_active: Boolean - Hiển thị hay ẩn
- order: Integer - Thứ tự hiển thị
```

### 2. Card (Thẻ flashcard)
```python
- id: Integer (Primary Key)
- deck_id: Integer (ForeignKey Deck.id)
- front_text: String(255) - "Dog", "Con chó"
- back_text: String(255) - Giải thích thêm
- image_url: String(300) - Hình minh họa
- audio_url: String(300) - File âm thanh (optional)
- order: Integer - Thứ tự trong bộ
- created_at: DateTime
```

### 3. CardProgress (Tiến độ từng thẻ - Anki algorithm)
```python
- id: Integer (Primary Key)
- child_id: Integer (ForeignKey Child.id)
- card_id: Integer (ForeignKey Card.id)
- ease_level: Integer (0=new, 1=hard, 2=good, 3=easy)
- repetitions: Integer - Số lần ôn
- next_review: DateTime - Thời điểm ôn lại
- last_reviewed: DateTime
- interval_days: Integer - Khoảng cách ôn (ngày)
```

### 4. DeckProgress (Tiến độ tổng thể)
```python
- id: Integer (Primary Key)
- child_id: Integer (ForeignKey Child.id)
- deck_id: Integer (ForeignKey Deck.id)
- learned_cards: Integer - Số thẻ đã học
- total_score: Integer - Tổng điểm
- stars: Integer - Số sao kiếm được
- last_studied: DateTime
- completion_date: DateTime - Ngày hoàn thành
- streak_days: Integer - Số ngày học liên tục
```

---

## 🎯 CÁCH SỬ DỤNG

### Cho giáo viên:

1. **Tạo bộ thẻ mới:**
   - Truy cập: http://localhost:5000/flashcards/admin
   - Click "➕ Tạo bộ thẻ mới"
   - Nhập tên, mô tả, chọn độ tuổi
   - Upload hình bìa (tùy chọn)
   - Click "✅ Tạo bộ thẻ"

2. **Thêm thẻ vào bộ:**
   - Click vào bộ thẻ → "📝 Quản lý thẻ"
   - Click "➕ Thêm thẻ mới"
   - Nhập từ (VD: "Dog", "Con chó")
   - Upload hình ảnh (JPG/PNG)
   - Upload audio (MP3/WAV) - nếu có
   - Click "✅ Thêm thẻ"

3. **Sửa/Xóa thẻ:**
   - Trong "Quản lý thẻ" → Click "🗑️ Xóa" để xóa thẻ

### Cho học sinh/trẻ em:

1. **Chọn độ tuổi:**
   - Truy cập: http://localhost:5000/flashcards/
   - Chọn 1 trong 3 nhóm tuổi

2. **Chọn bộ thẻ:**
   - Chọn bộ thẻ muốn học (Con vật, Màu sắc...)

3. **Chọn chế độ học:**
   - **Flash Mode**: Xem và nghe từng thẻ
   - **Quiz Mode**: Trả lời câu hỏi trắc nghiệm
   - **Audio Mode**: Nghe và chọn hình

4. **Nhận phần thưởng:**
   - Sau khi hoàn thành, nhận sao và sticker!

---

## 🎨 THIẾT KẾ GIAO DIỆN

### Màu sắc Pastel:
- **Mint**: #B2DFDB
- **Pink**: #F8BBD0
- **Yellow**: #FFF9C4
- **Blue**: #BBDEFB
- **Purple**: #E1BEE7
- **Peach**: #FFCCBC
- **Green**: #C8E6C9

### Typography:
- **Font**: Nunito (Google Fonts)
- **Title**: 2.5rem - 3rem
- **Body**: 1.2rem - 1.5rem
- **Button**: 1.3rem

### Spacing:
- **Border Radius**: 20px - 30px (bo tròn mềm mại)
- **Padding**: 20px - 40px
- **Gap**: 20px - 30px

---

## ⚙️ SPACED REPETITION ALGORITHM

Hệ thống sử dụng thuật toán tương tự Anki:

```python
def calculate_next_review(ease_level, current_interval=1):
    if ease_level == 0:  # New card
        return 1 day
    elif ease_level == 1:  # Hard
        return current_interval * 1.2
    elif ease_level == 2:  # Good
        return current_interval * 2.5
    elif ease_level == 3:  # Easy
        return current_interval * 3.5
    
    # Max interval: 365 days (1 năm)
```

---

## 🔧 TÙY CHỈNH

### Thay đổi giọng TTS:
File: `app/static/flashcard/flashcard.js`
```javascript
utterance.lang = 'vi-VN';  // Tiếng Việt
utterance.rate = 0.8;      // Tốc độ (0.5-1.0)
utterance.pitch = 1.2;     // Cao độ (0.5-2.0)
```

### Thay đổi số sao mỗi thẻ:
File: `app/static/flashcard/flashcard.js`
```javascript
const stars = this.learnedCards.size * 10;  // 10 sao/thẻ
```

### Thay đổi màu sắc:
File: `app/static/flashcard/flashcard.css`
```css
:root {
    --pastel-mint: #B2DFDB;
    --pastel-pink: #F8BBD0;
    /* ... */
}
```

---

## 📝 LƯU Ý

### Upload files:
- **Hình ảnh**: JPG, PNG, WEBP (nên dùng hình HD, rõ nét)
- **Audio**: MP3, WAV, M4A (ghi âm giọng cô giáo sẽ thân thiện hơn)
- Files được lưu tại: `app/static/flashcard/images/` và `app/static/flashcard/audio/`

### Bảo mật:
- Sử dụng `secure_filename()` để đặt tên file
- Thêm timestamp vào tên file tránh trùng lặp
- Kiểm tra extension trước khi upload

### Performance:
- Dùng FastImage (React Native) hoặc lazy loading cho hình ảnh
- Compress audio files trước khi upload
- Cache static files (CSS/JS)

---

## 🎉 HOÀN THÀNH!

Hệ thống flashcard đã sẵn sàng sử dụng! 

**Truy cập:**
- Học sinh: http://localhost:5000/flashcards/
- Giáo viên: http://localhost:5000/flashcards/admin

**Next steps:**
1. Chạy migration để tạo tables
2. Tạo bộ thẻ đầu tiên
3. Thêm thẻ vào bộ
4. Thử nghiệm 3 chế độ học
5. Deploy lên production!

---

## 📞 Hỗ trợ

Nếu gặp vấn đề, kiểm tra:
1. Database đã migrate chưa
2. Thư mục upload đã tạo chưa
3. Blueprint đã register trong `app/__init__.py` chưa
4. Static files có load được không (kiểm tra console browser)
