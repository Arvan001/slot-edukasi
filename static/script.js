document.addEventListener('DOMContentLoaded', function() {
    // Initialize game UI
    updateBalance();
    
    // Spin button event listener
    document.getElementById('spin-btn').addEventListener('click', spin);
});

let isSpinning = false;

async function spin() {
    if (isSpinning) return;
    isSpinning = true;
    
    const betInput = document.getElementById('bet-amount');
    const bet = parseInt(betInput.value);
    const resultDisplay = document.getElementById('result');
    const spinBtn = document.getElementById('spin-btn');
    
    // Validate bet
    if (isNaN(bet) || bet <= 0) {
        showError("Masukkan jumlah taruhan yang valid!");
        isSpinning = false;
        return;
    }
    
    try {
        spinBtn.disabled = true;
        resultDisplay.textContent = "Memutar...";
        
        // Start spinning animation
        startSpinAnimation();
        
        // Send spin request to server
        const response = await fetch('/api/spin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ bet: bet })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || "Gagal memutar!");
        }
        
        // Stop animation and show result
        stopSpinAnimation(data.result.status);
        
        if (data.result.status === "win") {
            resultDisplay.textContent = `MENANG! +${data.result.amount}`;
            resultDisplay.className = "result win";
            playWinSound();
        } else {
            resultDisplay.textContent = "COBA LAGI!";
            resultDisplay.className = "result lose";
        }
        
        // Update balance
        updateBalance(data.balance);
        
    } catch (error) {
        showError(error.message);
        console.error("Error:", error);
    } finally {
        spinBtn.disabled = false;
        isSpinning = false;
    }
}

function startSpinAnimation() {
    const reels = document.querySelectorAll('.reel');
    reels.forEach(reel => {
        reel.style.animation = "spin 0.5s infinite linear";
    });
}

function stopSpinAnimation(result) {
    const reels = document.querySelectorAll('.reel');
    const symbols = ["🍒", "🍋", "🍊", "🍇", "🍉", "💰"];
    
    reels.forEach((reel, index) => {
        setTimeout(() => {
            reel.style.animation = "none";
            reel.textContent = result === "win" ? "💰" : symbols[Math.floor(Math.random() * symbols.length)];
        }, 1000 * (index + 1));
    });
}

function updateBalance(balance) {
    document.getElementById('balance').textContent = balance;
}

function showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}

function playWinSound() {
    const audio = new Audio('/static/sounds/win.mp3');
    audio.play().catch(e => console.log("Audio error:", e));
}
