// === Pengaturan Admin ===
let pengaturan = {
  kemenanganSpin: {
    2: 100000,
    4: 100000
  },
  modeOtomatis: true,
  persentaseMenang: 20,
  minMenang: 50000,
  maxMenang: 100000
};

let saldo = 0;
let spinKe = 0;
let autoSpin = false;
let turboSpin = false;
let autoSpinInterval;
let isSpinning = false;
let autoSpinTarget = 0;
let autoSpinCounter = 0;

const reels = [
  document.querySelector("#r1 .reel-items"),
  document.querySelector("#r2 .reel-items"),
  document.querySelector("#r3 .reel-items")
];

const spinBtn = document.querySelector(".btn-spin");
const spinSound = document.getElementById("spinSound");
const winSound = document.getElementById("winSound");
const bgm = document.getElementById("bgm");
const saldoDisplay = document.getElementById("saldo");
const autoSpinInput = document.getElementById("autoSpinCount");

const simbol = ["🍒", "🍋", "🍊", "🔔", "⭐", "💎"];
const simbolMenang = ["💎", "⭐", "🔔"];

function formatRupiah(nilai) {
  return 'Rp ' + nilai.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

function tampilkanSaldo() {
  saldoDisplay.innerText = formatRupiah(saldo);
}

function playSound(sound) {
  sound.pause();
  sound.currentTime = 0;
  sound.play();
}

function spinReel(reel, hasilTengah, delay) {
  return new Promise(resolve => {
    const totalSimbol = 20;
    const tinggiSimbol = 50;
    const hasilIndex = totalSimbol - 2; // posisi tengah (baris ke-18 dari 20)

    let simbolAcak = [];
    for (let i = 0; i < totalSimbol; i++) {
      simbolAcak.push(simbol[Math.floor(Math.random() * simbol.length)]);
    }

    simbolAcak[hasilIndex - 1] = simbol[Math.floor(Math.random() * simbol.length)];
    simbolAcak[hasilIndex] = hasilTengah;
    simbolAcak[hasilIndex + 1] = simbol[Math.floor(Math.random() * simbol.length)];

    reel.innerHTML = simbolAcak.map((s, i) => {
      const tengah = i === hasilIndex;
      return `<div class="${tengah ? 'tengah-menang' : ''}">${s}</div>`;
    }).join('');

    reel.style.transition = "none";
    reel.style.transform = "translateY(0px)";

    setTimeout(() => {
      const jarakScroll = (hasilIndex - 1) * tinggiSimbol;
      reel.style.transition = `transform ${1 + delay}s ease-out`;
      reel.style.transform = `translateY(-${jarakScroll}px)`;
      setTimeout(resolve, (1 + delay) * 1000);
    }, 50);
  });
}

function showWinnerPopup(amount) {
  const popup = document.getElementById("winner-popup");
  const winAmount = document.getElementById("win-amount");
  winAmount.textContent = `+Rp ${amount.toLocaleString('id-ID')}`;
  popup.classList.remove("hidden");
  popup.classList.add("show");
  winSound.play();
  confetti({ particleCount: 200, spread: 100, origin: { y: 0.6 } });
}

function closeWinnerPopup() {
  const popup = document.getElementById("winner-popup");
  popup.classList.remove("show");
  popup.classList.add("hidden");
}

async function putar() {
  if (isSpinning) return;
  const taruhan = parseInt(document.getElementById("taruhan").value);
  if (taruhan > saldo || taruhan <= 0) {
    document.getElementById("pesan").innerText = "Taruhan tidak valid!";
    return;
  }

  isSpinning = true;
  spinBtn.disabled = true;
  spinBtn.style.opacity = 0.4;

  spinKe++;
  saldo -= taruhan;
  tampilkanSaldo();
  updateSaldoServer();
  document.getElementById("pesan").innerText = "";
  playSound(spinSound);

  let hasil = [null, null, null];
  let menang = 0;
  let simbolMenangFinal = simbolMenang[Math.floor(Math.random() * simbolMenang.length)];
  let bolehMenang = false;
  let jumlahMenang = 0;

  if (pengaturan.modeOtomatis) {
    await fetch("/should_win")
      .then(res => res.json())
      .then(data => {
        bolehMenang = data.bolehMenang;
        jumlahMenang = parseInt(data.jumlahMenang) || 0;
      })
      .catch(() => {
        bolehMenang = Math.random() * 100 < pengaturan.persentaseMenang;
        jumlahMenang = Math.floor(
          pengaturan.minMenang + Math.random() * (pengaturan.maxMenang - pengaturan.minMenang)
        );
      });
  } else {
    bolehMenang = pengaturan.kemenanganSpin.hasOwnProperty(spinKe);
    jumlahMenang = pengaturan.kemenanganSpin[spinKe] || taruhan * 5;
  }

  if (bolehMenang && jumlahMenang > 0) {
    hasil = [simbolMenangFinal, simbolMenangFinal, simbolMenangFinal];
    menang = jumlahMenang;
  } else {
    hasil = Array.from({ length: 3 }, () => simbol[Math.floor(Math.random() * simbol.length)]);
    if (hasil[0] === hasil[1] && hasil[1] === hasil[2]) {
      menang = taruhan * 5;
    }
  }

  await spinReel(reels[0], hasil[0], 0);
  await spinReel(reels[1], hasil[1], 0.2);
  await spinReel(reels[2], hasil[2], 0.4);

  if (menang > 0) {
    playSound(winSound);
    saldo += menang;
    tampilkanSaldo();
    updateSaldoServer();
    showWinnerPopup(menang);
    kirimLog("MENANG", menang);
  } else {
    document.getElementById("pesan").innerText = `😢 Kalah!`;
    kirimLog("KALAH", taruhan);
  }

  isSpinning = false;
  spinBtn.disabled = false;
  spinBtn.style.opacity = 1;

  if (autoSpin && (autoSpinTarget === 0 || autoSpinCounter < autoSpinTarget)) {
    autoSpinCounter++;
    autoSpinInterval = setTimeout(() => {
      putar();
    }, turboSpin ? 100 : 1000);
  } else if (autoSpinTarget > 0 && autoSpinCounter >= autoSpinTarget) {
    autoSpinToggle();
  }
}

function kirimLog(status, jumlah) {
  fetch("/log", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status, jumlah })
  }).catch(e => console.error("Gagal kirim log:", e));
}

function updateSaldoServer() {
  fetch("/api/update_saldo", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ saldo })
  }).catch(e => console.error("Gagal update saldo:", e));
}

function autoSpinToggle() {
  autoSpin = !autoSpin;
  autoSpinCounter = 0;
  autoSpinTarget = parseInt(autoSpinInput.value) || 0;
  document.getElementById("autoBtn").textContent = autoSpin ? "🔁 AUTO: ON" : "🔁 AUTO: OFF";
  if (autoSpin) putar();
  else clearTimeout(autoSpinInterval);
}

function turboSpinToggle() {
  turboSpin = !turboSpin;
  document.getElementById("turboBtn").textContent = turboSpin ? "⚡ TURBO: ON" : "⚡ TURBO: OFF";
}

window.addEventListener('DOMContentLoaded', () => {
  fetch("/api/saldo")
    .then(res => res.json())
    .then(data => {
      saldo = data.saldo;
      tampilkanSaldo();
    });

  fetch("/pengaturan")
    .then(res => res.json())
    .then(data => {
      pengaturan.modeOtomatis = data.modeOtomatis;
      pengaturan.persentaseMenang = data.persentaseMenang;
      pengaturan.minMenang = data.minMenang || 50000;
      pengaturan.maxMenang = data.maxMenang || 100000;
    });

  document.body.addEventListener('click', () => {
    bgm.volume = 0.3;
    bgm.play().catch(err => console.log("Autoplay ditolak:", err));
  }, { once: true });
});
