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
const winAmountDisplay = document.getElementById("win-amount");
const winnerText = document.getElementById("winner-text");

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

function spinReel(reel, hasil, delay) {
  return new Promise(resolve => {
    const totalSimbol = 30;
    const tinggiSimbol = 50;
    const offsetTengah = 50;

    let items = "";
    for (let i = 0; i < totalSimbol; i++) {
      const acak = simbol[Math.floor(Math.random() * simbol.length)];
      items += `<div>${acak}</div>`;
    }
    items += `<div>${hasil}</div>`;
    reel.innerHTML = items;

    reel.style.transition = "none";
    reel.style.transform = "translateY(0px)";

    setTimeout(() => {
      const totalScroll = totalSimbol * tinggiSimbol - offsetTengah;
      reel.style.transition = `transform ${1 + delay}s ease-out`;
      reel.style.transform = `translateY(-${totalScroll}px)`;
      setTimeout(resolve, (1 + delay) * 1000);
    }, 50);
  });
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
        jumlahMenang = data.jumlahMenang;
      })
      .catch(() => {
        bolehMenang = true;
        jumlahMenang = 50000;
      });
  } else {
    bolehMenang = pengaturan.kemenanganSpin.hasOwnProperty(spinKe);
    jumlahMenang = pengaturan.kemenanganSpin[spinKe] || taruhan * 5;
  }

  if (bolehMenang) {
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
    animateWinPopup(menang);
    kirimLog("MENANG", menang);
  } else {
    document.getElementById("pesan").innerText = `😢 Kalah!`;
    kirimLog("KALAH", taruhan);
  }

  isSpinning = false;
  spinBtn.disabled = false;
  spinBtn.style.opacity = 1;

  if (autoSpin) {
    autoSpinInterval = setTimeout(() => {
      putar();
    }, turboSpin ? 100 : 1000);
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

function animateWinPopup(jumlah) {
  const popup = document.getElementById("winner-popup");
  const coinRain = document.getElementById("coinRain");
  let current = 0;
  let durasi = Math.min(3000, 1000 + jumlah / 100); // makin besar makin lama
  let langkah = Math.ceil(jumlah / (durasi / 30));

  let judul = "🎉 WIN 🎉";
  if (jumlah >= 1000000) judul = "🔥 SUPER WIN 🔥";
  else if (jumlah >= 500000) judul = "💥 MEGA WIN 💥";
  else if (jumlah >= 100000) judul = "✨ BIG WIN ✨";

  winnerText.innerHTML = `<div class="bounce-text">${judul}</div><br><span id="win-amount">+Rp 0</span>`;

  popup.style.display = "flex";
  startFireworks();
  startCoinRain();

  const counter = setInterval(() => {
    current += langkah;
    if (current >= jumlah) {
      current = jumlah;
      clearInterval(counter);
      setTimeout(() => {
        popup.style.display = "none";
        stopFireworks();
        stopCoinRain();
      }, 1000); // tahan sebentar
    }
    winAmountDisplay.innerText = "+" + formatRupiah(current);
  }, 30);
}

function autoSpinToggle() {
  autoSpin = !autoSpin;
  document.getElementById("autoBtn").textContent = autoSpin ? "🔁 AUTO: ON" : "🔁 AUTO: OFF";
  if (autoSpin) putar();
  else clearTimeout(autoSpinInterval);
}

function turboSpinToggle() {
  turboSpin = !turboSpin;
  document.getElementById("turboBtn").textContent = turboSpin ? "⚡ TURBO: ON" : "⚡ TURBO: OFF";
}

function startCoinRain() {
  const container = document.getElementById("coinRain");
  container.innerHTML = "";
  container.style.display = "block";
  for (let i = 0; i < 50; i++) {
    const coin = document.createElement("div");
    coin.className = "coin";
    coin.style.left = Math.random() * 100 + "%";
    coin.style.animationDelay = Math.random() + "s";
    container.appendChild(coin);
  }
}

function stopCoinRain() {
  const container = document.getElementById("coinRain");
  container.innerHTML = "";
  container.style.display = "none";
}

let fwCanvas = document.getElementById("fireworks");
let ctx = fwCanvas.getContext("2d");
let particles = [];
let intervalId;

function resizeCanvas() {
  fwCanvas.width = window.innerWidth;
  fwCanvas.height = window.innerHeight;
}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();

function random(min, max) {
  return Math.random() * (max - min) + min;
}

function createParticle() {
  const colors = ["#ff0", "#f00", "#0f0", "#0ff", "#f0f", "#fff"];
  return {
    x: fwCanvas.width / 2,
    y: fwCanvas.height / 2,
    vx: random(-5, 5),
    vy: random(-5, 5),
    size: random(2, 5),
    color: colors[Math.floor(Math.random() * colors.length)],
    life: 60
  };
}

function updateParticles() {
  ctx.clearRect(0, 0, fwCanvas.width, fwCanvas.height);
  for (let i = particles.length - 1; i >= 0; i--) {
    let p = particles[i];
    p.x += p.vx;
    p.y += p.vy;
    p.life--;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.size, 0, 2 * Math.PI);
    ctx.fillStyle = p.color;
    ctx.fill();
    if (p.life <= 0) particles.splice(i, 1);
  }
}

function loopFireworks() {
  particles.push(...Array.from({ length: 5 }, createParticle));
  updateParticles();
}

function startFireworks() {
  intervalId = setInterval(loopFireworks, 50);
}

function stopFireworks() {
  clearInterval(intervalId);
  ctx.clearRect(0, 0, fwCanvas.width, fwCanvas.height);
  particles = [];
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
