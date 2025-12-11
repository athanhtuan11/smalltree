// ================== FLASHCARD JAVASCRIPT - HOWLER.JS + ANIME.JS ==================

// Khởi tạo Howler.js cho TTS tiếng Việt
const tts = {
    speak: function(text) {
        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'vi-VN';
            utterance.rate = 0.8;  // Chậm hơn cho trẻ em
            utterance.pitch = 1.2;  // Cao độ cao hơn, dễ nghe
            window.speechSynthesis.speak(utterance);
        }
    },
    
    stop: function() {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
        }
    }
};

// Phát audio file với Howler.js
function playAudio(audioPath) {
    if (!audioPath) {
        console.warn('No audio path provided');
        return;
    }
    
    // Fix path if needed
    const fixedPath = audioPath.includes('/') ? `/static/flashcard/audio/${audioPath.split('/').pop()}` : `/static/flashcard/audio/${audioPath}`;
    
    const sound = new Howl({
        src: [fixedPath],
        html5: true,
        onloaderror: function(id, error) {
            console.error('Error loading audio:', error);
            // Fallback to text-to-speech if audio fails
        },
        onplayerror: function(id, error) {
            console.error('Error playing audio:', error);
        }
    });
    
    sound.play();
}

// ================== FLASH MODE ==================
class FlashMode {
    constructor(cards, childId) {
        // Shuffle các thẻ để tăng tư duy
        this.cards = this.shuffleArray([...cards]);
        this.childId = childId;
        this.currentIndex = 0;
        this.learnedCards = new Set();
        this.currentSound = null;
        
        this.init();
    }
    
    shuffleArray(array) {
        const shuffled = [...array];
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        return shuffled;
    }
    
    init() {
        this.render();
        this.updateProgress();
        
        // Auto-play audio khi hiển thị thẻ
        setTimeout(() => this.playCurrentCard(), 500);
    }
    
    render() {
        const card = this.cards[this.currentIndex];
        const container = document.getElementById('flashcard-content');
        
        const imagePath = card.image_url.includes('/') ? `/static/${card.image_url}` : `/static/flashcard/images/${card.image_url}`;
        
        container.innerHTML = `
            <div class="flashcard fade-in">
                <img src="${imagePath}" class="card-image" alt="${card.front_text}">
                <div class="card-text">${card.front_text}</div>
                ${card.back_text ? `<div class="card-subtext">${card.back_text}</div>` : ''}
                <button class="sound-btn" onclick="flashMode.playCurrentCard()">🔊</button>
            </div>
            
            <div class="controls">
                <button class="btn-control btn-prev" onclick="flashMode.prev()" ${this.currentIndex === 0 ? 'disabled' : ''}>
                    ⬅️ Quay lại
                </button>
                <button class="btn-control btn-next" onclick="flashMode.next()">
                    ${this.currentIndex === this.cards.length - 1 ? '✅ Hoàn thành' : 'Tiếp theo ➡️'}
                </button>
            </div>
        `;
        
        // Animation
        anime({
            targets: '.flashcard',
            scale: [0.8, 1],
            opacity: [0, 1],
            duration: 500,
            easing: 'easeOutElastic(1, .8)'
        });
    }
    
    playCurrentCard() {
        const card = this.cards[this.currentIndex];
        
        // Dừng audio/TTS cũ trước khi phát mới
        if (this.currentSound) {
            this.currentSound.stop();
            this.currentSound = null;
        }
        tts.stop();
        
        // Phát audio nếu có, không thì dùng TTS
        if (card.audio_url) {
            const audioPath = card.audio_url.includes('/') ? `/static/${card.audio_url}` : `/static/flashcard/audio/${card.audio_url}`;
            this.currentSound = new Howl({
                src: [audioPath],
                html5: true,
                onloaderror: (id, error) => {
                    console.error('Audio load error:', error);
                    tts.speak(card.front_text);
                }
            });
            this.currentSound.play();
        } else {
            tts.speak(card.front_text);
        }
        
        // Animation nút
        anime({
            targets: '.sound-btn',
            scale: [1, 1.2, 1],
            duration: 300,
            easing: 'easeInOutQuad'
        });
        
        // Đánh dấu đã học
        this.learnedCards.add(card.id);
        this.updateProgress();
    }
    
    next() {
        // Dừng audio/TTS hiện tại
        if (this.currentSound) {
            this.currentSound.stop();
            this.currentSound = null;
        }
        tts.stop();
        
        if (this.currentIndex === this.cards.length - 1) {
            this.finish();
        } else {
            this.currentIndex++;
            this.render();
            setTimeout(() => this.playCurrentCard(), 500);
        }
    }
    
    prev() {
        // Dừng audio/TTS hiện tại
        if (this.currentSound) {
            this.currentSound.stop();
            this.currentSound = null;
        }
        tts.stop();
        
        if (this.currentIndex > 0) {
            this.currentIndex--;
            this.render();
        }
    }
    
    updateProgress() {
        const progressBar = document.querySelector('.progress-fill');
        const counter = document.querySelector('.card-counter');
        
        if (progressBar) {
            const percent = ((this.currentIndex + 1) / this.cards.length) * 100;
            progressBar.style.width = `${percent}%`;
        }
        
        if (counter) {
            counter.textContent = `${this.currentIndex + 1} / ${this.cards.length}`;
        }
    }
    
    finish() {
        // Dừng audio/TTS hiện tại
        if (this.currentSound) {
            this.currentSound.stop();
            this.currentSound = null;
        }
        tts.stop();
        
        const stars = this.learnedCards.size * 10;
        
        // Lưu tiến độ
        if (this.childId) {
            this.saveProgress(stars);
        }
        
        // Chuyển đến màn hình phần thưởng
        const deckId = this.cards[0].deck_id;
        window.location.href = `/flashcards/rewards?child_id=${this.childId || ''}&deck_id=${deckId}&stars=${stars}`;
    }
    
    saveProgress(stars) {
        fetch('/flashcards/api/update-deck-progress', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                child_id: this.childId,
                deck_id: this.cards[0].deck_id,
                learned_cards: this.learnedCards.size,
                stars: stars
            })
        });
    }
}

// ================== QUIZ MODE ==================
class QuizMode {
    constructor(cards, childId) {
        // Shuffle các thẻ để tăng tư duy
        this.cards = this.shuffleArray([...cards]);
        this.childId = childId;
        this.currentIndex = 0;
        this.score = 0;
        this.totalStars = 0;
        
        this.init();
    }
    
    shuffleArray(array) {
        const shuffled = [...array];
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        return shuffled;
    }
    
    init() {
        console.log('QuizMode initialized with', this.cards.length, 'cards (shuffled)');
        this.renderQuestion();
    }
    
    renderQuestion() {
        const card = this.cards[this.currentIndex];
        const container = document.getElementById('quiz-content');
        
        console.log('Rendering question for card:', card);
        
        // Tạo 3 đáp án: 1 đúng + 2 sai (random)
        const options = this.generateOptions(card);
        console.log('Generated options:', options);
        
        // Hiển thị hình ảnh câu hỏi
        const questionImagePath = card.image_url.includes('/') ? `/static/${card.image_url}` : `/static/flashcard/images/${card.image_url}`;
        
        // Tạo options chỉ có tên (không có hình)
        const optionsHTML = options.map((opt, idx) => {
            return `
                <div class="quiz-option text-only" onclick="quizMode.checkAnswer(${opt.id}, ${card.id}, this)">
                    <p style="font-size: 1.5rem; font-weight: bold; margin: 0;">${opt.front_text}</p>
                </div>
            `;
        }).join('');
        
        container.innerHTML = `
            <div class="quiz-question fade-in">
                <h2>Đây là ${card.front_text.toLowerCase().includes('con ') ? 'con vật' : card.front_text.toLowerCase().includes('quả ') || card.front_text.toLowerCase().includes('trái ') ? 'trái cây' : card.front_text.toLowerCase().includes('màu ') ? 'màu sắc' : card.front_text.toLowerCase().includes('số ') ? 'con số' : card.front_text.toLowerCase().includes('chữ ') ? 'chữ cái' : 'hình'} gì? 🤔</h2>
                <div style="margin: 30px auto; max-width: 400px;">
                    <img src="${questionImagePath}" alt="?" style="width: 100%; border-radius: 20px; box-shadow: 0 8px 20px rgba(0,0,0,0.2);">
                </div>
                <div class="score-display">
                    <span class="stars">⭐</span> ${this.totalStars}
                </div>
            </div>
            
            <div class="quiz-options" style="display: flex; flex-direction: column; gap: 15px; max-width: 500px; margin: 0 auto;">
                ${optionsHTML}
            </div>
        `;
        
        console.log('Quiz HTML rendered');
        this.updateProgress();
    }
    
    generateOptions(correctCard) {
        const options = [correctCard];
        const otherCards = this.cards.filter(c => c.id !== correctCard.id);
        
        // Chọn random 2 thẻ khác
        while (options.length < 3 && otherCards.length > 0) {
            const randomIndex = Math.floor(Math.random() * otherCards.length);
            options.push(otherCards[randomIndex]);
            otherCards.splice(randomIndex, 1);
        }
        
        // Shuffle
        return options.sort(() => Math.random() - 0.5);
    }
    
    checkAnswer(selectedId, correctId, element) {
        const isCorrect = selectedId === correctId;
        
        if (isCorrect) {
            element.classList.add('correct');
            this.score += 10;
            this.totalStars += 10;
            
            // Phát pháo hoa 🎉
            confetti({
                particleCount: 100,
                spread: 70,
                origin: { y: 0.6 }
            });
            
            // Phát âm thanh đúng
            tts.speak('Đúng rồi! Giỏi lắm!');
            
        } else {
            element.classList.add('wrong');
            
            // Animation rung
            anime({
                targets: element,
                translateX: [
                    { value: -10, duration: 50 },
                    { value: 10, duration: 50 },
                    { value: -10, duration: 50 },
                    { value: 10, duration: 50 },
                    { value: 0, duration: 50 }
                ],
                easing: 'linear'
            });
            
            tts.speak('Chưa đúng, thử lại nhé!');
        }
        
        // Disable các nút khác
        document.querySelectorAll('.quiz-option').forEach(opt => {
            opt.style.pointerEvents = 'none';
        });
        
        // Tự động chuyển câu sau 2 giây
        setTimeout(() => {
            this.nextQuestion();
        }, 2000);
    }
    
    nextQuestion() {
        if (this.currentIndex < this.cards.length - 1) {
            this.currentIndex++;
            this.renderQuestion();
        } else {
            this.finish();
        }
    }
    
    updateProgress() {
        const progressBar = document.querySelector('.progress-fill');
        const counter = document.querySelector('.card-counter');
        
        if (progressBar) {
            const percent = ((this.currentIndex + 1) / this.cards.length) * 100;
            progressBar.style.width = `${percent}%`;
        }
        
        if (counter) {
            counter.textContent = `${this.currentIndex + 1} / ${this.cards.length}`;
        }
    }
    
    finish() {
        if (this.childId) {
            this.saveProgress();
        }
        
        const deckId = this.cards[0].deck_id;
        window.location.href = `/flashcards/rewards?child_id=${this.childId || ''}&deck_id=${deckId}&stars=${this.totalStars}`;
    }
    
    saveProgress() {
        fetch('/flashcards/api/update-deck-progress', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                child_id: this.childId,
                deck_id: this.cards[0].deck_id,
                learned_cards: this.cards.length,
                score: this.score,
                stars: this.totalStars
            })
        });
    }
}

// ================== AUDIO MODE ==================
class AudioMode {
    constructor(cards, childId) {
        // Shuffle các thẻ để tăng tư duy
        this.cards = this.shuffleArray([...cards]);
        this.childId = childId;
        this.currentIndex = 0;
        this.score = 0;
        this.totalStars = 0;
        this.currentSound = null;
        
        this.init();
    }
    
    shuffleArray(array) {
        const shuffled = [...array];
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        return shuffled;
    }
    
    init() {
        this.renderQuestion();
        this.autoPlay();
    }
    
    renderQuestion() {
        const card = this.cards[this.currentIndex];
        const container = document.getElementById('audio-content');
        
        const options = this.generateOptions(card);
        
        const optionsHTML = options.map((opt, idx) => {
            const imagePath = opt.image_url.includes('/') ? `/static/${opt.image_url}` : `/static/flashcard/images/${opt.image_url}`;
            return `
                <div class="quiz-option" onclick="audioMode.checkAnswer(${opt.id}, ${card.id}, this)">
                    <img src="${imagePath}" alt="${opt.front_text}">
                </div>
            `;
        }).join('');
        
        container.innerHTML = `
            <div class="audio-player fade-in">
                <div class="icon">🎧</div>
                <h2>Nghe và chọn hình đúng!</h2>
                <button class="btn-replay" onclick="audioMode.replay()">🔊</button>
                <div class="score-display">
                    <span class="stars">⭐</span> ${this.totalStars}
                </div>
            </div>
            
            <div class="quiz-options">
                ${optionsHTML}
            </div>
        `;
        
        this.updateProgress();
    }
    
    generateOptions(correctCard) {
        const options = [correctCard];
        const otherCards = this.cards.filter(c => c.id !== correctCard.id);
        
        while (options.length < 3 && otherCards.length > 0) {
            const randomIndex = Math.floor(Math.random() * otherCards.length);
            options.push(otherCards[randomIndex]);
            otherCards.splice(randomIndex, 1);
        }
        
        return options.sort(() => Math.random() - 0.5);
    }
    
    autoPlay() {
        setTimeout(() => this.playAudio(), 800);
    }
    
    playAudio() {
        const card = this.cards[this.currentIndex];
        
        // Dừng audio và TTS cũ
        if (this.currentSound) {
            this.currentSound.stop();
        }
        tts.stop();
        
        if (card.audio_url) {
            const audioPath = card.audio_url.includes('/') ? `/static/${card.audio_url}` : `/static/flashcard/audio/${card.audio_url}`;
            this.currentSound = new Howl({
                src: [audioPath],
                html5: true,
                onloaderror: (id, error) => {
                    console.error('Audio load error:', error, 'Path:', audioPath);
                    tts.speak(card.front_text);
                }
            });
            this.currentSound.play();
        } else {
            tts.speak(card.front_text);
        }
        
        // Animation nút replay
        anime({
            targets: '.btn-replay',
            scale: [1, 1.2, 1],
            rotate: [0, 360],
            duration: 600,
            easing: 'easeInOutQuad'
        });
    }
    
    replay() {
        this.playAudio();
    }
    
    checkAnswer(selectedId, correctId, element) {
        const isCorrect = selectedId === correctId;
        
        if (isCorrect) {
            element.classList.add('correct');
            this.score += 10;
            this.totalStars += 10;
            
            confetti({
                particleCount: 100,
                spread: 70,
                origin: { y: 0.6 }
            });
            
            tts.speak('Đúng rồi!');
            
        } else {
            element.classList.add('wrong');
            anime({
                targets: element,
                translateX: [
                    { value: -10, duration: 50 },
                    { value: 10, duration: 50 },
                    { value: -10, duration: 50 },
                    { value: 10, duration: 50 },
                    { value: 0, duration: 50 }
                ],
                easing: 'linear'
            });
        }
        
        document.querySelectorAll('.quiz-option').forEach(opt => {
            opt.style.pointerEvents = 'none';
        });
        
        setTimeout(() => {
            this.nextQuestion();
        }, 2000);
    }
    
    nextQuestion() {
        // Dừng audio/TTS hiện tại
        if (this.currentSound) {
            this.currentSound.stop();
            this.currentSound = null;
        }
        tts.stop();
        
        if (this.currentIndex < this.cards.length - 1) {
            this.currentIndex++;
            this.renderQuestion();
            this.autoPlay();
        } else {
            this.finish();
        }
    }
    
    updateProgress() {
        const progressBar = document.querySelector('.progress-fill');
        const counter = document.querySelector('.card-counter');
        
        if (progressBar) {
            const percent = ((this.currentIndex + 1) / this.cards.length) * 100;
            progressBar.style.width = `${percent}%`;
        }
        
        if (counter) {
            counter.textContent = `${this.currentIndex + 1} / ${this.cards.length}`;
        }
    }
    
    finish() {
        // Dừng audio/TTS hiện tại
        if (this.currentSound) {
            this.currentSound.stop();
            this.currentSound = null;
        }
        tts.stop();
        
        if (this.childId) {
            this.saveProgress();
        }
        
        const deckId = this.cards[0].deck_id;
        window.location.href = `/flashcards/rewards?child_id=${this.childId || ''}&deck_id=${deckId}&stars=${this.totalStars}`;
    }
    
    saveProgress() {
        fetch('/flashcards/api/update-deck-progress', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                child_id: this.childId,
                deck_id: this.cards[0].deck_id,
                learned_cards: this.cards.length,
                score: this.score,
                stars: this.totalStars
            })
        });
    }
}

// ================== CONFETTI LIBRARY (lightweight) ==================
function confetti(options) {
    const defaults = {
        particleCount: 50,
        spread: 60,
        origin: { x: 0.5, y: 0.5 }
    };
    
    const config = { ...defaults, ...options };
    
    for (let i = 0; i < config.particleCount; i++) {
        createParticle(config);
    }
}

function createParticle(config) {
    const particle = document.createElement('div');
    particle.style.position = 'fixed';
    particle.style.width = '10px';
    particle.style.height = '10px';
    particle.style.backgroundColor = ['#FFD700', '#FF69B4', '#00CED1', '#FF6347', '#9370DB'][Math.floor(Math.random() * 5)];
    particle.style.borderRadius = '50%';
    particle.style.pointerEvents = 'none';
    particle.style.zIndex = '9999';
    
    const startX = window.innerWidth * config.origin.x;
    const startY = window.innerHeight * config.origin.y;
    
    particle.style.left = startX + 'px';
    particle.style.top = startY + 'px';
    
    document.body.appendChild(particle);
    
    const angle = (Math.random() * config.spread - config.spread / 2) * Math.PI / 180;
    const velocity = 5 + Math.random() * 10;
    
    anime({
        targets: particle,
        translateX: Math.cos(angle) * velocity * 50,
        translateY: [0, -200 + Math.random() * 100, window.innerHeight],
        opacity: [1, 1, 0],
        rotate: Math.random() * 720,
        duration: 3000,
        easing: 'easeOutCubic',
        complete: () => {
            particle.remove();
        }
    });
}

// ================== UTILITY FUNCTIONS ==================
function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
}
