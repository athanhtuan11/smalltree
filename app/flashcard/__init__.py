"""
Flashcard Blueprint - Hệ thống học flashcard cho trẻ mầm non
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from app.models import db, Deck, Card, CardProgress, DeckProgress, Child
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os
from functools import wraps

# Cloudflare R2 Storage
try:
    from r2_storage import get_r2_storage
    R2_ENABLED = True
    r2 = get_r2_storage()
except ImportError:
    R2_ENABLED = False
    print("⚠️  R2 Storage không khả dụng cho Flashcard. Ảnh sẽ lưu local.")

flashcard_bp = Blueprint('flashcard', __name__, url_prefix='/flashcards', template_folder='templates')

UPLOAD_FOLDER = 'app/static/flashcard'
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a'}

def allowed_file(filename, extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions

def admin_required(f):
    """Decorator để kiểm tra quyền admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('role') or session.get('role') != 'admin':
            flash('Bạn cần quyền admin để truy cập trang này', 'error')
            return redirect(url_for('flashcard.index'))
        return f(*args, **kwargs)
    return decorated_function

# ================== SPACED REPETITION ALGORITHM (Anki-style) ==================
def calculate_next_review(ease_level, current_interval=1):
    """Tính khoảng cách ôn tập tiếp theo"""
    if ease_level == 0:  # New card
        return 1, datetime.now() + timedelta(days=1)
    elif ease_level == 1:  # Hard
        new_interval = max(1, current_interval * 1.2)
    elif ease_level == 2:  # Good
        new_interval = current_interval * 2.5
    elif ease_level == 3:  # Easy
        new_interval = current_interval * 3.5
    else:
        new_interval = 1
    
    new_interval = min(new_interval, 365)  # Max 1 năm
    next_review_date = datetime.now() + timedelta(days=new_interval)
    return int(new_interval), next_review_date

# ================== TRANG CHỦ FLASHCARD ==================
@flashcard_bp.route('/')
def index():
    """Trang chủ - Chọn độ tuổi"""
    return render_template('flashcard/index.html')

@flashcard_bp.route('/age/<age_group>')
def deck_list(age_group):
    """Danh sách bộ thẻ theo độ tuổi"""
    if age_group not in ['1-3', '3-5', '5-7']:
        flash('Độ tuổi không hợp lệ', 'error')
        return redirect(url_for('flashcard.index'))
    
    decks = Deck.query.filter_by(age_group=age_group, is_active=True).order_by(Deck.order).all()
    return render_template('flashcard/deck_list.html', decks=decks, age_group=age_group)

@flashcard_bp.route('/deck/<int:deck_id>')
def deck_detail(deck_id):
    """Chi tiết bộ thẻ - Chọn chế độ học"""
    deck = Deck.query.get_or_404(deck_id)
    cards_count = Card.query.filter_by(deck_id=deck_id).count()
    
    # Lấy tiến độ nếu đã đăng nhập
    child_id = request.args.get('child_id', type=int)
    progress = None
    if child_id:
        progress = DeckProgress.query.filter_by(child_id=child_id, deck_id=deck_id).first()
    
    return render_template('flashcard/deck_detail.html', deck=deck, cards_count=cards_count, progress=progress)

# ================== CHẾ ĐỘ HỌC ==================
@flashcard_bp.route('/learn/<int:deck_id>')
def learn_flash(deck_id):
    """Flash Mode - Xem thẻ và nghe phát âm"""
    deck = Deck.query.get_or_404(deck_id)
    cards = Card.query.filter_by(deck_id=deck_id).order_by(Card.order).all()
    child_id = request.args.get('child_id', type=int)
    
    return render_template('flashcard/learn_flash.html', deck=deck, cards=cards, child_id=child_id)

@flashcard_bp.route('/quiz/<int:deck_id>')
def learn_quiz(deck_id):
    """Quiz Mode - Trắc nghiệm 3 đáp án"""
    deck = Deck.query.get_or_404(deck_id)
    cards = Card.query.filter_by(deck_id=deck_id).order_by(Card.order).all()
    
    if len(cards) < 3:
        flash(f'Quiz Mode cần ít nhất 3 thẻ. Hiện tại chỉ có {len(cards)} thẻ. Vui lòng thêm thẻ!', 'warning')
        return redirect(url_for('flashcard.deck_detail', deck_id=deck_id))
    
    child_id = request.args.get('child_id', type=int)
    return render_template('flashcard/learn_quiz.html', deck=deck, cards=cards, child_id=child_id)

@flashcard_bp.route('/audio/<int:deck_id>')
def learn_audio(deck_id):
    """Audio Mode - Nghe và chọn hình"""
    deck = Deck.query.get_or_404(deck_id)
    cards = Card.query.filter_by(deck_id=deck_id).order_by(Card.order).all()
    
    # Lọc chỉ lấy thẻ có audio
    cards_with_audio = [c for c in cards if c.audio_url]
    
    if len(cards_with_audio) < 3:
        flash(f'Audio Mode cần ít nhất 3 thẻ có file âm thanh. Hiện tại có {len(cards_with_audio)}/{len(cards)} thẻ có audio. Vui lòng upload thêm audio!', 'warning')
        return redirect(url_for('flashcard.deck_detail', deck_id=deck_id))
    
    child_id = request.args.get('child_id', type=int)
    return render_template('flashcard/learn_audio.html', deck=deck, cards=cards_with_audio, child_id=child_id)

@flashcard_bp.route('/rewards')
def rewards():
    """Màn hình phần thưởng"""
    child_id = request.args.get('child_id', type=int)
    stars = request.args.get('stars', 0, type=int)
    deck_id = request.args.get('deck_id', type=int)
    
    deck = Deck.query.get(deck_id) if deck_id else None
    progress = None
    
    if child_id and deck_id:
        progress = DeckProgress.query.filter_by(child_id=child_id, deck_id=deck_id).first()
    
    return render_template('flashcard/rewards.html', stars=stars, deck=deck, progress=progress, child_id=child_id)

# ================== API CHO JAVASCRIPT ==================
@flashcard_bp.route('/api/update-progress', methods=['POST'])
def update_progress():
    """Cập nhật tiến độ học của học sinh"""
    data = request.json
    child_id = data.get('child_id')
    card_id = data.get('card_id')
    ease_level = data.get('ease_level', 2)
    
    if not child_id or not card_id:
        return jsonify({'success': False, 'message': 'Missing data'}), 400
    
    # Tìm hoặc tạo progress
    progress = CardProgress.query.filter_by(child_id=child_id, card_id=card_id).first()
    
    if not progress:
        progress = CardProgress(child_id=child_id, card_id=card_id)
        db.session.add(progress)
    
    # Tính toán khoảng cách ôn tập
    new_interval, next_review = calculate_next_review(ease_level, progress.interval_days)
    
    progress.ease_level = ease_level
    progress.repetitions += 1
    progress.interval_days = new_interval
    progress.next_review = next_review
    progress.last_reviewed = datetime.now()
    
    db.session.commit()
    
    return jsonify({'success': True, 'next_review': next_review.isoformat()})

@flashcard_bp.route('/api/update-deck-progress', methods=['POST'])
def update_deck_progress():
    """Cập nhật tiến độ tổng thể của bộ thẻ"""
    data = request.json
    child_id = data.get('child_id')
    deck_id = data.get('deck_id')
    learned_cards = data.get('learned_cards', 0)
    score = data.get('score', 0)
    stars = data.get('stars', 0)
    
    if not child_id or not deck_id:
        return jsonify({'success': False, 'message': 'Missing data'}), 400
    
    progress = DeckProgress.query.filter_by(child_id=child_id, deck_id=deck_id).first()
    
    if not progress:
        progress = DeckProgress(child_id=child_id, deck_id=deck_id)
        db.session.add(progress)
    
    progress.learned_cards = learned_cards
    progress.total_score += score
    progress.stars += stars
    progress.last_studied = datetime.now()
    
    # Kiểm tra hoàn thành
    total_cards = Card.query.filter_by(deck_id=deck_id).count()
    if learned_cards >= total_cards and not progress.completion_date:
        progress.completion_date = datetime.now()
    
    # Cập nhật streak
    if progress.last_studied:
        days_diff = (datetime.now().date() - progress.last_studied.date()).days
        if days_diff == 1:
            progress.streak_days += 1
        elif days_diff > 1:
            progress.streak_days = 1
    else:
        progress.streak_days = 1
    
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'total_stars': progress.stars,
        'streak': progress.streak_days
    })

# ================== ADMIN - QUẢN LÝ FLASHCARD ==================
@flashcard_bp.route('/admin')
@admin_required
def admin():
    """Trang quản lý flashcard cho giáo viên"""
    decks = Deck.query.order_by(Deck.age_group, Deck.order).all()
    return render_template('flashcard/admin.html', decks=decks)

@flashcard_bp.route('/admin/deck/create', methods=['GET', 'POST'])
@admin_required
def create_deck():
    """Tạo bộ thẻ mới"""
    if request.method == 'POST':
        print(f"[DEBUG] Form data: {request.form}")
        print(f"[DEBUG] CSRF token in form: {request.form.get('csrf_token')}")
        title = request.form.get('title')
        description = request.form.get('description')
        age_group = request.form.get('age_group')
        
        # Upload cover image
        cover_image = None
        if 'cover_image' in request.files:
            file = request.files['cover_image']
            if file and allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
                filename = f"{timestamp}_{filename}"
                
                # Upload to R2 hoặc local fallback
                if R2_ENABLED:
                    try:
                        r2_path = f"flashcard/covers/{filename}"
                        file.seek(0)
                        r2.upload_file(file, r2_path)
                        cover_image = f"{r2.public_url}/{r2_path}"
                        print(f"✅ Uploaded cover to R2: {cover_image}")
                    except Exception as e:
                        print(f"⚠️  R2 upload failed, saving local: {e}")
                        os.makedirs(os.path.join(UPLOAD_FOLDER, 'images'), exist_ok=True)
                        file.seek(0)
                        file.save(os.path.join(UPLOAD_FOLDER, 'images', filename))
                        cover_image = f"flashcard/images/{filename}"
                else:
                    os.makedirs(os.path.join(UPLOAD_FOLDER, 'images'), exist_ok=True)
                    file.save(os.path.join(UPLOAD_FOLDER, 'images', filename))
                    cover_image = f"flashcard/images/{filename}"
        
        deck = Deck(
            title=title,
            description=description,
            age_group=age_group,
            cover_image=cover_image,
            created_by=1  # TODO: Lấy từ session
        )
        
        db.session.add(deck)
        db.session.commit()
        
        flash(f'Đã tạo bộ thẻ "{title}"', 'success')
        return redirect(url_for('flashcard.admin'))
    
    return render_template('flashcard/create_deck.html')

@flashcard_bp.route('/admin/deck/<int:deck_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_deck(deck_id):
    """Sửa bộ thẻ"""
    deck = Deck.query.get_or_404(deck_id)
    
    if request.method == 'POST':
        deck.title = request.form.get('title')
        deck.description = request.form.get('description')
        deck.age_group = request.form.get('age_group')
        deck.is_active = request.form.get('is_active') == 'on'
        
        # Upload cover image mới
        if 'cover_image' in request.files:
            file = request.files['cover_image']
            if file and allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
                filename = f"{timestamp}_{filename}"
                file.save(os.path.join(UPLOAD_FOLDER, 'images', filename))
                deck.cover_image = f"flashcard/images/{filename}"
        
        db.session.commit()
        flash(f'Đã cập nhật bộ thẻ "{deck.title}"', 'success')
        return redirect(url_for('flashcard.admin'))
    
    return render_template('flashcard/edit_deck.html', deck=deck)

@flashcard_bp.route('/admin/deck/<int:deck_id>/cards')
@admin_required
def manage_cards(deck_id):
    """Quản lý thẻ trong bộ"""
    deck = Deck.query.get_or_404(deck_id)
    cards = Card.query.filter_by(deck_id=deck_id).order_by(Card.order).all()
    return render_template('flashcard/manage_cards.html', deck=deck, cards=cards)

@flashcard_bp.route('/admin/deck/<int:deck_id>/card/create', methods=['GET', 'POST'])
@admin_required
def create_card(deck_id):
    """Tạo thẻ mới trong bộ"""
    deck = Deck.query.get_or_404(deck_id)
    
    if request.method == 'POST':
        front_text = request.form.get('front_text')
        back_text = request.form.get('back_text')
        
        # Upload image
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
                filename = f"{timestamp}_{filename}"
                
                # Upload to R2 hoặc local fallback
                if R2_ENABLED:
                    try:
                        r2_path = f"flashcard/cards/{filename}"
                        file.seek(0)
                        r2.upload_file(file, r2_path)
                        image_url = f"{r2.public_url}/{r2_path}"
                        print(f"✅ Uploaded card image to R2: {image_url}")
                    except Exception as e:
                        print(f"⚠️  R2 upload failed, saving local: {e}")
                        os.makedirs(os.path.join(UPLOAD_FOLDER, 'images'), exist_ok=True)
                        file.seek(0)
                        file.save(os.path.join(UPLOAD_FOLDER, 'images', filename))
                        image_url = f"flashcard/images/{filename}"
                else:
                    os.makedirs(os.path.join(UPLOAD_FOLDER, 'images'), exist_ok=True)
                    file.save(os.path.join(UPLOAD_FOLDER, 'images', filename))
                    image_url = f"flashcard/images/{filename}"
        
        # Upload audio
        audio_url = None
        if 'audio' in request.files:
            file = request.files['audio']
            if file and allowed_file(file.filename, ALLOWED_AUDIO_EXTENSIONS):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
                filename = f"{timestamp}_{filename}"
                
                # Upload to R2 hoặc local fallback
                if R2_ENABLED:
                    try:
                        r2_path = f"flashcard/audio/{filename}"
                        file.seek(0)
                        r2.upload_file(file, r2_path)
                        audio_url = f"{r2.public_url}/{r2_path}"
                        print(f"✅ Uploaded audio to R2: {audio_url}")
                    except Exception as e:
                        print(f"⚠️  R2 upload failed, saving local: {e}")
                        os.makedirs(os.path.join(UPLOAD_FOLDER, 'audio'), exist_ok=True)
                        file.seek(0)
                        file.save(os.path.join(UPLOAD_FOLDER, 'audio', filename))
                        audio_url = f"flashcard/audio/{filename}"
                else:
                    os.makedirs(os.path.join(UPLOAD_FOLDER, 'audio'), exist_ok=True)
                    file.save(os.path.join(UPLOAD_FOLDER, 'audio', filename))
                    audio_url = f"flashcard/audio/{filename}"
        
        # Lấy order cao nhất
        max_order = db.session.query(db.func.max(Card.order)).filter_by(deck_id=deck_id).scalar() or 0
        
        card = Card(
            deck_id=deck_id,
            front_text=front_text,
            back_text=back_text,
            image_url=image_url,
            audio_url=audio_url,
            order=max_order + 1
        )
        
        db.session.add(card)
        db.session.commit()
        
        flash(f'Đã thêm thẻ "{front_text}"', 'success')
        return redirect(url_for('flashcard.manage_cards', deck_id=deck_id))
    
    return render_template('flashcard/create_card.html', deck=deck)

@flashcard_bp.route('/admin/card/<int:card_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_card(card_id):
    """Sửa thẻ"""
    card = Card.query.get_or_404(card_id)
    deck = Deck.query.get_or_404(card.deck_id)
    
    if request.method == 'POST':
        card.front_text = request.form.get('front_text')
        card.back_text = request.form.get('back_text')
        
        # Upload hình mới nếu có
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
                filename = f"{timestamp}_{filename}"
                
                # Upload to R2 hoặc local fallback
                if R2_ENABLED:
                    try:
                        r2_path = f"flashcard/cards/{filename}"
                        file.seek(0)
                        r2.upload_file(file, r2_path)
                        card.image_url = f"{r2.public_url}/{r2_path}"
                        print(f"✅ Updated card image on R2: {card.image_url}")
                    except Exception as e:
                        print(f"⚠️  R2 upload failed, saving local: {e}")
                        os.makedirs(os.path.join(UPLOAD_FOLDER, 'images'), exist_ok=True)
                        file.seek(0)
                        file.save(os.path.join(UPLOAD_FOLDER, 'images', filename))
                        card.image_url = f"flashcard/images/{filename}"
                else:
                    os.makedirs(os.path.join(UPLOAD_FOLDER, 'images'), exist_ok=True)
                    file.save(os.path.join(UPLOAD_FOLDER, 'images', filename))
                    card.image_url = f"flashcard/images/{filename}"
        
        # Upload audio mới nếu có
        if 'audio' in request.files:
            file = request.files['audio']
            if file and allowed_file(file.filename, ALLOWED_AUDIO_EXTENSIONS):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
                filename = f"{timestamp}_{filename}"
                
                # Upload to R2 hoặc local fallback
                if R2_ENABLED:
                    try:
                        r2_path = f"flashcard/audio/{filename}"
                        file.seek(0)
                        r2.upload_file(file, r2_path)
                        card.audio_url = f"{r2.public_url}/{r2_path}"
                        print(f"✅ Updated audio on R2: {card.audio_url}")
                    except Exception as e:
                        print(f"⚠️  R2 upload failed, saving local: {e}")
                        os.makedirs(os.path.join(UPLOAD_FOLDER, 'audio'), exist_ok=True)
                        file.seek(0)
                        file.save(os.path.join(UPLOAD_FOLDER, 'audio', filename))
                        card.audio_url = f"flashcard/audio/{filename}"
                else:
                    os.makedirs(os.path.join(UPLOAD_FOLDER, 'audio'), exist_ok=True)
                    file.save(os.path.join(UPLOAD_FOLDER, 'audio', filename))
                    card.audio_url = f"flashcard/audio/{filename}"
        
        db.session.commit()
        flash(f'Đã cập nhật thẻ "{card.front_text}"', 'success')
        return redirect(url_for('flashcard.manage_cards', deck_id=card.deck_id))
    
    return render_template('flashcard/edit_card.html', card=card, deck=deck)

@flashcard_bp.route('/admin/card/<int:card_id>/delete', methods=['POST'])
@admin_required
def delete_card(card_id):
    """Xóa thẻ"""
    card = Card.query.get_or_404(card_id)
    deck_id = card.deck_id
    
    db.session.delete(card)
    db.session.commit()
    
    flash(f'Đã xóa thẻ "{card.front_text}"', 'success')
    return redirect(url_for('flashcard.manage_cards', deck_id=deck_id))
