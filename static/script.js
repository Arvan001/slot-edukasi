class SlotGame {
    constructor() {
        this.balance = 0;
        this.betAmount = 10000;
        this.isSpinning = false;
        this.autoSpin = false;
        this.turboMode = false;
        this.autoSpinCount = 0;
        this.maxAutoSpins = 5;
        
        this.symbols = ['7', 'cherry', 'lemon', 'orange', 'grape', 'watermelon', 'diamond'];
        this.symbolElements = {
            '7': '<div class="symbol symbol-7">7</div>',
            'cherry': '<div class="symbol symbol-cherry">🍒</div>',
            'lemon': '<div class="symbol symbol-lemon">🍋</div>',
            'orange': '<div class="symbol symbol-orange">🍊</div>',
            'grape': '<div class="symbol symbol-grape">🍇</div>',
            'watermelon': '<div class="symbol symbol-watermelon">🍉</div>',
            'diamond': '<div class="symbol symbol-diamond">💎</div>'
        };
        
        this.initElements();
        this.initEventListeners();
        this.loadUserData();
        this.initReels();
    }

    initElements() {
        this.elements = {
            reels: [
                document.getElementById('reel1'),
                document.getElementById('reel2'),
                document.getElementById('reel3')
            ],
            balanceDisplay: document.getElementById('saldo'),
            betInput: document.getElementById('taruhan'),
            messageDisplay: document.getElementById('pesan'),
            spinBtn: document.getElementById('spinBtn'),
            autoBtn: document.getElementById('autoBtn'),
            turboBtn: document.getElementById('turboBtn'),
            autoSpinInput: document.getElementById('autoSpinCount'),
            popup: document.getElementById('winner-popup'),
            winAmountDisplay: document.getElementById('win-amount'),
            closePopupBtn: document.getElementById('closePopupBtn'),
            bgm: document.getElementById('bgm')
        };
    }

    initEventListeners() {
        this.elements.spinBtn.addEventListener('click', () => this.handleSpin());
        this.elements.autoBtn.addEventListener('click', () => this.toggleAutoSpin());
        this.elements.turboBtn.addEventListener('click', () => this.toggleTurboMode());
        this.elements.closePopupBtn.addEventListener('click', () => this.closePopup());
        this.elements.betInput.addEventListener('change', () => this.updateBetAmount());
        this.elements.autoSpinInput.addEventListener('change', () => this.updateAutoSpinCount());
        
        // Enable audio on first interaction
        document.body.addEventListener('click', () => {
            this.elements.bgm.play().catch(e => console.log("Audio autoplay prevented:", e));
        }, { once: true });
    }

    initReels() {
        // Create 20 symbols for each reel (5 visible + buffer)
        for (let i = 0; i < 20; i++) {
            this.elements.reels.forEach(reel => {
                const randomSymbol = this.symbols[Math.floor(Math.random() * this.symbols.length)];
                reel.innerHTML += this.symbolElements[randomSymbol];
            });
        }
    }

    updateBetAmount() {
        this.betAmount = Math.max(1000, 
            Math.min(
                parseInt(this.elements.betInput.value) || 10000, 
                100000
            )
        );
        this.elements.betInput.value = this.betAmount;
    }

    updateAutoSpinCount() {
        this.maxAutoSpins = Math.max(1, 
            Math.min(
                parseInt(this.elements.autoSpinInput.value) || 5, 
                100
            )
        );
        this.elements.autoSpinInput.value = this.maxAutoSpins;
    }

    async loadUserData() {
        try {
            const response = await fetch('/api/user', {
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                credentials: 'include'  // Important for session cookies
            });
            
            if (!response.ok) {
                // If unauthorized, redirect to login
                if (response.status === 401) {
                    window.location.href = '/login';
                    return;
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            if (data.success) {
                this.balance = data.saldo;
                this.updateUI();
            } else {
                throw new Error(data.error || 'Failed to load user data');
            }
        } catch (error) {
            console.error('Error loading user data:', error);
            this.showMessage('Gagal memuat data pengguna');
            // Redirect to login if not authenticated
            if (error.message.includes('401')) {
                window.location.href = '/login';
            }
        }
    }

    async handleSpin() {
        if (this.isSpinning) return;
        
        // Validate bet
        if (this.betAmount <= 0 || this.betAmount > this.balance) {
            this.showMessage('Jumlah taruhan tidak valid');
            return;
        }

        this.isSpinning = true;
        this.disableButtons();
        
        try {
            // Start spin animation
            this.showMessage('Memutar...');
            await this.animateSpin();
            
            // Send spin request to server
            const response = await fetch('/api/spin', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ bet: this.betAmount }),
                credentials: 'include'  // Important for session cookies
            });
            
            if (!response.ok) {
                if (response.status === 401) {
                    window.location.href = '/login';
                    return;
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            if (!result.success) {
                throw new Error(result.error || 'Gagal memutar');
            }
            
            // Update game state
            this.balance = result.new_balance;
            
            // Handle win/loss
            if (result.result.win) {
                this.showWin(result.result.amount);
            } else {
                this.showMessage('Coba lagi!');
            }
            
            this.updateUI();
            
            // If auto-spin is active and we haven't reached max spins
            if (this.autoSpin && this.autoSpinCount < this.maxAutoSpins) {
                this.autoSpinCount++;
                setTimeout(() => this.handleSpin(), 1000);
            } else {
                this.autoSpinCount = 0;
                if (this.autoSpin) {
                    this.toggleAutoSpin(); // Turn off auto-spin when max spins reached
                }
            }
            
        } catch (error) {
            console.error('Spin error:', error);
            this.showMessage(error.message || 'Terjadi kesalahan saat memutar');
        } finally {
            this.isSpinning = false;
            this.enableButtons();
        }
    }

    async animateSpin() {
        const spinDuration = this.turboMode ? 1000 : 3000;
        const startTime = Date.now();
        
        // Randomize final positions
        const finalPositions = this.elements.reels.map(() => 
            -Math.floor(Math.random() * 15 + 5) * 100
        );
        
        // Play spin sound
        const spinSound = new Audio('/static/sounds/spin.mp3');
        spinSound.play().catch(e => console.log("Audio error:", e));
        
        return new Promise((resolve) => {
            const animate = () => {
                const elapsed = Date.now() - startTime;
                const progress = Math.min(elapsed / spinDuration, 1);
                
                // Update reel positions
                this.elements.reels.forEach((reel, index) => {
                    const startPos = 0;
                    const endPos = finalPositions[index];
                    const currentPos = startPos + (endPos - startPos) * progress;
                    reel.style.transform = `translateY(${currentPos}px)`;
                });
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                } else {
                    resolve();
                }
            };
            
            animate();
        });
    }

    showWin(amount) {
        this.elements.winAmountDisplay.textContent = `+Rp ${amount.toLocaleString('id-ID')}`;
        this.elements.popup.classList.add('visible');
        
        // Confetti effect
        confetti({
            particleCount: 150,
            spread: 70,
            origin: { y: 0.6 }
        });
        
        // Play win sound
        const winSound = new Audio('/static/sounds/win.mp3');
        winSound.play().catch(e => console.log("Audio error:", e));
        
        // Auto-close popup after 3 seconds
        setTimeout(() => {
            this.closePopup();
        }, 3000);
    }

    closePopup() {
        this.elements.popup.classList.remove('visible');
    }

    toggleAutoSpin() {
        this.autoSpin = !this.autoSpin;
        this.autoSpinCount = 0;
        
        if (this.autoSpin) {
            this.elements.autoBtn.textContent = '🔁 AUTO: ON';
            this.elements.autoBtn.classList.add('active');
            if (!this.isSpinning) {
                this.handleSpin();
            }
        } else {
            this.elements.autoBtn.textContent = '🔁 AUTO: OFF';
            this.elements.autoBtn.classList.remove('active');
        }
    }

    toggleTurboMode() {
        this.turboMode = !this.turboMode;
        
        if (this.turboMode) {
            this.elements.turboBtn.textContent = '⚡ TURBO: ON';
            this.elements.turboBtn.classList.add('active');
        } else {
            this.elements.turboBtn.textContent = '⚡ TURBO: OFF';
            this.elements.turboBtn.classList.remove('active');
        }
    }

    updateUI() {
        this.elements.balanceDisplay.textContent = `Rp ${this.balance.toLocaleString('id-ID')}`;
        this.elements.betInput.value = this.betAmount;
    }

    showMessage(message) {
        this.elements.messageDisplay.textContent = message;
    }

    disableButtons() {
        this.elements.spinBtn.disabled = true;
        this.elements.autoBtn.disabled = true;
        this.elements.turboBtn.disabled = true;
    }

    enableButtons() {
        this.elements.spinBtn.disabled = false;
        this.elements.autoBtn.disabled = false;
        this.elements.turboBtn.disabled = false;
    }
}

// Initialize game when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Check if we're on the game page
    if (document.getElementById('spinBtn')) {
        window.slotGame = new SlotGame();
        
        // Try to play background music (will be muted until user interaction)
        const bgm = document.getElementById('bgm');
        bgm.volume = 0.5;
        bgm.play().catch(e => console.log("BGM autoplay prevented:", e));
    }
});
