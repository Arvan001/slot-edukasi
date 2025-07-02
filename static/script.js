class SlotGame {
    constructor() {
        this.balance = 0;
        this.betAmount = 10000;
        this.isSpinning = false;
        this.autoSpin = false;
        this.turboMode = false;
        this.lastUpdate = null;
        
        this.initElements();
        this.initEventListeners();
        this.loadUserData();
        
        // Auto-save every 30 seconds
        setInterval(() => this.saveUserData(), 30000);
    }

    initElements() {
        this.elements = {
            // Game elements
            reels: Array.from(document.querySelectorAll('.reel-items')),
            reelHighlight: document.querySelector('.reel-highlight'),
            
            // UI elements
            balanceDisplay: document.getElementById('saldo'),
            betInput: document.getElementById('taruhan'),
            messageDisplay: document.getElementById('pesan'),
            
            // Buttons
            spinBtn: document.getElementById('spinBtn'),
            autoBtn: document.getElementById('autoBtn'),
            turboBtn: document.getElementById('turboBtn'),
            
            // Popup
            popup: document.getElementById('winner-popup'),
            winAmountDisplay: document.getElementById('win-amount'),
            closePopupBtn: document.getElementById('closePopupBtn')
        };
    }

    initEventListeners() {
        // Button events
        this.elements.spinBtn.addEventListener('click', () => this.handleSpin());
        this.elements.autoBtn.addEventListener('click', () => this.toggleAutoSpin());
        this.elements.turboBtn.addEventListener('click', () => this.toggleTurboMode());
        this.elements.closePopupBtn.addEventListener('click', () => this.closePopup());
        
        // Bet input validation
        this.elements.betInput.addEventListener('change', () => {
            this.betAmount = Math.max(1000, 
                Math.min(
                    parseInt(this.elements.betInput.value) || 10000, 
                    500000
                )
            );
            this.elements.betInput.value = this.betAmount;
        });
        
        // Save data before unload
        window.addEventListener('beforeunload', () => this.saveUserData());
    }

    async loadUserData() {
        try {
            const response = await fetch('/api/user');
            if (!response.ok) throw new Error('Failed to load user data');
            
            const data = await response.json();
            this.balance = data.saldo;
            this.lastUpdate = data.last_update;
            this.updateUI();
        } catch (error) {
            console.error('Error loading user data:', error);
            this.showMessage('Gagal memuat data pengguna');
        }
    }

    async saveUserData() {
        try {
            await fetch('/api/user', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ saldo: this.balance })
            });
        } catch (error) {
            console.error('Error saving user data:', error);
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
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ bet: this.betAmount })
            });
            
            const result = await response.json();
            if (!result.success) {
                throw new Error(result.error || 'Unknown error');
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
            
        } catch (error) {
            console.error('Spin error:', error);
            this.showMessage('Terjadi kesalahan saat memutar');
        } finally {
            this.isSpinning = false;
            this.enableButtons();
        }
    }

    async animateSpin() {
        // Simple spin animation - replace with your actual animation logic
        const spinDuration = this.turboMode ? 1000 : 2000;
        const startTime = Date.now();
        
        // Animation loop
        return new Promise((resolve) => {
            const animate = () => {
                const elapsed = Date.now() - startTime;
                const progress = Math.min(elapsed / spinDuration, 1);
                
                // Update reel positions
                this.elements.reels.forEach((reel, index) => {
                    const offset = Math.sin(progress * Math.PI * 2 + index * 0.5) * 100;
                    reel.style.transform = `translateY(${offset}px)`;
                });
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                } else {
                    // Reset reels to center position
                    this.elements.reels.forEach(reel => {
                        reel.style.transform = 'translateY(0)';
                    });
                    resolve();
                }
            };
            
            animate();
        });
    }

    showWin(amount) {
        this.elements.winAmountDisplay.textContent = `+Rp ${amount.toLocaleString('id-ID')}`;
        this.elements.popup.classList.add('visible');
        
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
        this.elements.autoBtn.textContent = this.autoSpin ? 'AUTO: ON' : 'AUTO: OFF';
        
        if (this.autoSpin && !this.isSpinning) {
            this.handleSpin();
        }
    }

    toggleTurboMode() {
        this.turboMode = !this.turboMode;
        this.elements.turboBtn.textContent = this.turboMode ? 'TURBO: ON' : 'TURBO: OFF';
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
    window.slotGame = new SlotGame();
});
