class SlotGame {
  constructor() {
    this.balance = 0;
    this.isSpinning = false;
    this.autoSpin = false;
    this.autoSpinCount = 0;
    this.turboMode = false;
    this.userId = localStorage.getItem('user_id') || `user_${Math.random().toString(36).substr(2, 9)}`;
    
    this.initElements();
    this.initEventListeners();
    this.loadBalance();
  }

  initElements() {
    this.elements = {
      reels: Array.from(document.querySelectorAll('.reel-items')),
      balanceDisplay: document.getElementById('saldo'),
      betInput: document.getElementById('taruhan'),
      messageDisplay: document.getElementById('pesan'),
      spinBtn: document.getElementById('spinBtn'),
      autoBtn: document.getElementById('autoBtn'),
      turboBtn: document.getElementById('turboBtn'),
      popup: document.getElementById('winner-popup'),
      winAmountDisplay: document.getElementById('win-amount'),
      closePopupBtn: document.getElementById('closePopupBtn')
    };
  }

  initEventListeners() {
    this.elements.spinBtn.addEventListener('click', () => this.spin());
    this.elements.autoBtn.addEventListener('click', () => this.toggleAutoSpin());
    this.elements.turboBtn.addEventListener('click', () => this.toggleTurboMode());
    this.elements.closePopupBtn.addEventListener('click', () => this.closePopup());
    
    // Save user ID
    if (!localStorage.getItem('user_id')) {
      localStorage.setItem('user_id', this.userId);
    }
  }

  async loadBalance() {
    try {
      const response = await fetch('/api/balance');
      const data = await response.json();
      this.balance = data.saldo;
      this.updateBalanceDisplay();
    } catch (error) {
      console.error('Failed to load balance:', error);
      this.showMessage('Gagal memuat saldo, menggunakan saldo default');
      this.balance = 100000;
      this.updateBalanceDisplay();
    }
  }

  async spin() {
    if (this.isSpinning) return;
    
    const betAmount = parseInt(this.elements.betInput.value) || 0;
    
    // Validate bet
    if (betAmount <= 0 || betAmount > this.balance) {
      this.showMessage('Taruhan tidak valid!');
      return;
    }

    this.isSpinning = true;
    this.balance -= betAmount;
    this.updateBalanceDisplay();
    this.showMessage('');
    
    // Disable buttons during spin
    this.elements.spinBtn.disabled = true;
    this.elements.autoBtn.disabled = true;
    
    try {
      // Check win condition from server
      const winResponse = await fetch('/api/should_win');
      const winData = await winResponse.json();
      
      // Spin animation
      const spinResult = await this.animateSpin(winData.bolehMenang ? winData.jumlahMenang : 0);
      
      // Update balance if won
      if (spinResult.winAmount > 0) {
        this.balance += spinResult.winAmount;
        this.updateBalanceDisplay();
        this.showWinPopup(spinResult.winAmount);
      }
      
      // Log the spin result
      await this.logSpin(spinResult.winAmount > 0 ? 'MENANG' : 'KALAH', 
                        spinResult.winAmount > 0 ? spinResult.winAmount : betAmount);
      
    } catch (error) {
      console.error('Spin error:', error);
      this.showMessage('Terjadi kesalahan saat spin');
    } finally {
      this.isSpinning = false;
      this.elements.spinBtn.disabled = false;
      this.elements.autoBtn.disabled = false;
      
      // Continue auto spin if enabled
      if (this.autoSpin && this.autoSpinCount > 0) {
        this.autoSpinCount--;
        setTimeout(() => this.spin(), this.turboMode ? 200 : 1000);
      }
    }
  }

  async animateSpin(winAmount) {
    const targetSymbol = winAmount > 0 ? 
      ['💎', '⭐', '🔔', '7️⃣'][Math.floor(Math.random() * 4)] : 
      ['🍒', '🍋', '🍊', '🔔', '⭐', '💎', '7️⃣'][Math.floor(Math.random() * 7)];
    
    // Animate each reel sequentially
    for (let i = 0; i < this.elements.reels.length; i++) {
      await this.animateReel(this.elements.reels[i], targetSymbol, i * 0.2);
    }
    
    // Check if all reels match (for visual win)
    const reelSymbols = this.elements.reels.map(reel => reel.children[1].textContent);
    const visualWin = reelSymbols[0] === reelSymbols[1] && reelSymbols[1] === reelSymbols[2];
    
    return {
      winAmount: visualWin ? winAmount : 0,
      symbols: reelSymbols
    };
  }

  animateReel(reel, targetSymbol, delay) {
    return new Promise(resolve => {
      const symbolHeight = 100 / 3; // 3 visible symbols
      const spinDuration = 1 + Math.random() * 0.5;
      
      // Create spinning effect
      let spinSymbols = '';
      for (let i = 0; i < 15; i++) {
        spinSymbols += `<div>${['🍒', '🍋', '🍊', '🔔', '⭐', '💎', '7️⃣'][Math.floor(Math.random() * 7)]}</div>`;
      }
      
      reel.innerHTML = spinSymbols + `<div>${targetSymbol}</div>`;
      reel.style.transition = `transform ${spinDuration}s cubic-bezier(0.1, 0.7, 0.1, 1)`;
      reel.style.transform = `translateY(-${100 - symbolHeight}%)`;
      
      setTimeout(() => {
        // Show final symbols
        reel.innerHTML = `
          <div>${['🍒', '🍋', '🍊', '🔔', '⭐', '💎', '7️⃣'][Math.floor(Math.random() * 7)]}</div>
          <div>${targetSymbol}</div>
          <div>${['🍒', '🍋', '🍊', '🔔', '⭐', '💎', '7️⃣'][Math.floor(Math.random() * 7)]}</div>
        `;
        reel.style.transition = 'none';
        reel.style.transform = `translateY(-${symbolHeight}%)`;
        resolve();
      }, spinDuration * 1000);
    });
  }

  toggleAutoSpin() {
    this.autoSpin = !this.autoSpin;
    this.elements.autoBtn.textContent = this.autoSpin ? "🔁 AUTO: ON" : "🔁 AUTO: OFF";
    this.autoSpinCount = this.autoSpin ? 10 : 0;
    
    if (this.autoSpin && !this.isSpinning) {
      this.spin();
    }
  }

  toggleTurboMode() {
    this.turboMode = !this.turboMode;
    this.elements.turboBtn.textContent = this.turboMode ? "⚡ TURBO: ON" : "⚡ TURBO: OFF";
  }

  async logSpin(status, amount) {
    try {
      await fetch('/api/log', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          status: status,
          jumlah: amount
        })
      });
    } catch (error) {
      console.error('Failed to log spin:', error);
    }
  }

  async updateBalanceDisplay() {
    this.elements.balanceDisplay.textContent = `Rp ${this.balance.toLocaleString('id-ID')}`;
    
    // Save balance to server
    try {
      await fetch('/api/balance', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          saldo: this.balance
        })
      });
    } catch (error) {
      console.error('Failed to update balance:', error);
    }
  }

  showMessage(message) {
    this.elements.messageDisplay.textContent = message;
  }

  showWinPopup(amount) {
    this.elements.winAmountDisplay.textContent = `+Rp ${amount.toLocaleString('id-ID')}`;
    this.elements.popup.classList.add('show');
  }

  closePopup() {
    this.elements.popup.classList.remove('show');
  }
}

// Initialize the game when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new SlotGame();
});
