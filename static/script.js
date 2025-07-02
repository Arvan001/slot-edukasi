// Game Configuration
const config = {
  symbols: ["🍒", "🍋", "🍊", "🔔", "⭐", "💎", "7️⃣"],
  winningSymbols: ["💎", "⭐", "🔔", "7️⃣"],
  winMultipliers: {
    "💎": 10,
    "⭐": 5,
    "🔔": 3,
    "7️⃣": 15
  }
};

// Game State
let balance = 100000;
let isSpinning = false;
let autoSpin = false;
let autoSpinCount = 0;
let currentBet = 10000;

// DOM Elements
const reels = Array.from(document.querySelectorAll('.reel-items'));
const balanceDisplay = document.getElementById('saldo');
const betInput = document.getElementById('taruhan');
const messageDisplay = document.getElementById('pesan');
const spinBtn = document.getElementById('spinBtn');
const autoBtn = document.getElementById('autoBtn');
const turboBtn = document.getElementById('turboBtn');
const popup = document.getElementById('winner-popup');
const winAmountDisplay = document.getElementById('win-amount');
const closePopupBtn = document.getElementById('closePopupBtn');

// Initialize Game
function initGame() {
  updateBalance();
  initializeReels();
  setupEventListeners();
}

// Initialize reels with visible symbols
function initializeReels() {
  reels.forEach(reel => {
    let symbolsHTML = '';
    for (let i = 0; i < 3; i++) {
      const randomSymbol = config.symbols[
        Math.floor(Math.random() * config.symbols.length)
      ];
      symbolsHTML += `<div>${randomSymbol}</div>`;
    }
    reel.innerHTML = symbolsHTML;
    reel.style.transform = 'translateY(-33.33%)';
  });
}

// Spin a single reel
function spinReel(reel, targetSymbol, delay) {
  return new Promise(resolve => {
    const symbolHeight = 100 / 3; // 3 visible symbols
    const spinDuration = 1 + Math.random() * 0.5;
    
    // Create spinning effect
    let spinSymbols = '';
    for (let i = 0; i < 15; i++) {
      spinSymbols += `<div>${config.symbols[
        Math.floor(Math.random() * config.symbols.length)
      ]}</div>`;
    }
    
    reel.innerHTML = spinSymbols + `<div>${targetSymbol}</div>`;
    reel.style.transition = `transform ${spinDuration}s cubic-bezier(0.1, 0.7, 0.1, 1)`;
    reel.style.transform = `translateY(-${100 - symbolHeight}%)`;
    
    setTimeout(() => {
      // Show final symbols
      reel.innerHTML = `
        <div>${config.symbols[Math.floor(Math.random() * config.symbols.length)]}</div>
        <div>${targetSymbol}</div>
        <div>${config.symbols[Math.floor(Math.random() * config.symbols.length)]}</div>
      `;
      reel.style.transition = 'none';
      reel.style.transform = `translateY(-${symbolHeight}%)`;
      resolve();
    }, spinDuration * 1000);
  });
}

// Main spin function
async function spin() {
  if (isSpinning) return;
  
  currentBet = parseInt(betInput.value) || 10000;
  if (currentBet > balance || currentBet <= 0) {
    showMessage("Taruhan tidak valid!");
    return;
  }

  isSpinning = true;
  balance -= currentBet;
  updateBalance();
  showMessage("");
  
  // Determine win condition
  const shouldWin = Math.random() < 0.3; // 30% win chance
  const winSymbol = shouldWin 
    ? config.winningSymbols[
        Math.floor(Math.random() * config.winningSymbols.length)
      ] 
    : config.symbols[Math.floor(Math.random() * config.symbols.length)];

  // Spin reels sequentially
  await spinReel(reels[0], winSymbol, 0);
  await spinReel(reels[1], winSymbol, 0.1);
  await spinReel(reels[2], winSymbol, 0.2);

  // Check win
  const reelSymbols = reels.map(reel => 
    reel.children[1].textContent
  );
  
  if (reelSymbols[0] === reelSymbols[1] && reelSymbols[1] === reelSymbols[2]) {
    const winAmount = currentBet * (
      config.winMultipliers[reelSymbols[0]] || 2
    );
    balance += winAmount;
    updateBalance();
    showWinPopup(winAmount);
  } else {
    showMessage("Coba lagi!");
  }

  isSpinning = false;
  
  // Continue auto spin if active
  if (autoSpin && autoSpinCount > 0) {
    autoSpinCount--;
    setTimeout(spin, 500);
  }
}

// UI Functions
function updateBalance() {
  balanceDisplay.textContent = `Rp ${balance.toLocaleString('id-ID')}`;
}

function showMessage(msg) {
  messageDisplay.textContent = msg;
}

function showWinPopup(amount) {
  winAmountDisplay.textContent = `+Rp ${amount.toLocaleString('id-ID')}`;
  popup.classList.add('show');
}

function closePopup() {
  popup.classList.remove('show');
}

// Event Listeners
function setupEventListeners() {
  spinBtn.addEventListener('click', spin);
  closePopupBtn.addEventListener('click', closePopup);
  
  autoBtn.addEventListener('click', () => {
    autoSpin = !autoSpin;
    autoBtn.textContent = autoSpin ? "🔁 AUTO: ON" : "🔁 AUTO: OFF";
    autoSpinCount = autoSpin ? 10 : 0;
  });
  
  turboBtn.addEventListener('click', () => {
    turboSpin = !turboSpin;
    turboBtn.textContent = turboSpin ? "⚡ TURBO: ON" : "⚡ TURBO: OFF";
  });
}

// Start the game
initGame();
