class SlotGame {
    constructor() {
        this.balance = 0;
        this.betAmount = 10000;
        this.isSpinning = false;
        
        // Inisialisasi elemen UI
        this.initElements();
        this.initEventListeners();
        
        // Load data user saat pertama kali
        this.loadUserData().then(() => {
            this.updateUI();
        }).catch(error => {
            console.error("Gagal memuat data user:", error);
            this.showMessage("Gagal memuat data pengguna");
        });
    }

    initElements() {
        this.elements = {
            balanceDisplay: document.getElementById('saldo'),
            betInput: document.getElementById('taruhan'),
            messageDisplay: document.getElementById('pesan'),
            spinBtn: document.getElementById('spinBtn'),
            reels: [
                document.getElementById('reel1'),
                document.getElementById('reel2'),
                document.getElementById('reel3')
            ]
        };
        
        // Debug: Cek apakah elemen ditemukan
        console.log("Elemen yang ditemukan:", this.elements);
    }

    initEventListeners() {
        // Pasang event listener untuk tombol spin
        this.elements.spinBtn.addEventListener('click', () => {
            console.log("Tombol spin diklik");
            this.handleSpin();
        });
        
        // Update nilai taruhan saat diubah
        this.elements.betInput.addEventListener('change', () => {
            this.betAmount = parseInt(this.elements.betInput.value) || 10000;
        });
    }

    async loadUserData() {
        try {
            console.log("Memulai load data user...");
            const response = await fetch('/api/user');
            
            if (!response.ok) {
                throw new Error(`Error HTTP! Status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log("Data user diterima:", data);
            
            if (data.success) {
                this.balance = data.saldo;
            } else {
                throw new Error(data.error || "Gagal memuat data user");
            }
        } catch (error) {
            console.error("Error dalam loadUserData:", error);
            throw error;
        }
    }

    async handleSpin() {
        // Cek apakah sedang spinning
        if (this.isSpinning) {
            console.log("Spin sedang berjalan, abaikan klik");
            return;
        }
        
        // Validasi saldo
        if (this.betAmount > this.balance) {
            this.showMessage("Saldo tidak mencukupi!");
            return;
        }
        
        this.isSpinning = true;
        this.disableButtons();
        this.showMessage("Memutar...");
        
        try {
            console.log("Memulai proses spin...");
            
            // Kirim request ke server
            const response = await fetch('/api/spin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ bet: this.betAmount })
            });
            
            if (!response.ok) {
                throw new Error(`Error HTTP! Status: ${response.status}`);
            }
            
            const result = await response.json();
            console.log("Hasil spin:", result);
            
            if (result.success) {
                // Update saldo
                this.balance = result.new_balance;
                this.updateUI();
                
                // Tampilkan hasil
                if (result.result.win) {
                    this.showMessage(`MENANG! +${result.result.amount}`);
                } else {
                    this.showMessage("Coba lagi!");
                }
            } else {
                throw new Error(result.error || "Gagal memutar");
            }
        } catch (error) {
            console.error("Error dalam handleSpin:", error);
            this.showMessage("Terjadi kesalahan saat memutar");
        } finally {
            this.isSpinning = false;
            this.enableButtons();
        }
    }

    updateUI() {
        console.log("Memperbarui UI, saldo:", this.balance);
        this.elements.balanceDisplay.textContent = `Rp ${this.balance.toLocaleString('id-ID')}`;
        this.elements.betInput.value = this.betAmount;
    }

    showMessage(message) {
        this.elements.messageDisplay.textContent = message;
    }

    disableButtons() {
        this.elements.spinBtn.disabled = true;
    }

    enableButtons() {
        this.elements.spinBtn.disabled = false;
    }
}

// Inisialisasi game saat halaman siap
document.addEventListener('DOMContentLoaded', () => {
    console.log("Dokumen siap, inisialisasi game...");
    window.slotGame = new SlotGame();
});
