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
const saldoDisplay = document.getElementById("saldo");
const winPopup = document.getElementById("winner-popup");
const winAmount = document.getElementById("win-amount");

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
    const tinggiSimbol = 50;
    const simbolList = [];

    for (let i = 0; i < 10; i++) {
      simbolList.push(`<div>${simbol[Math.floor(Math.random() * simbol.length)]}</div>`);
    }

    simbolList.push(`<div>${simbol[Math.floor(Math.random() * simbol.length)]}</div>`); // atas
    simbolList.push(`<div class='winning'>${hasil}</div>`); // tengah
    simbolList.push(`<div>${simbol[Math.floor(Math.random() * simbol.length)]}</div>`); // bawah

    reel.innerHTML = simbolList.join("");

    reel.style.transition = "none";
    reel.style.transform = `translateY(0px)`;

    setTimeout(() => {
      const posisiTengah = (simbolList.length - 2) * tinggiSimbol;
      reel.style.transition = `transform ${1 + delay}s ease-out`;
      reel.style.transform = `translateY(-${posisiTengah}px)`;
      setTimeout(resolve, (1 + delay) * 1000);
    }, 50);
  });
}

function showWinnerPopup(jumlah) {
  winAmount.innerText = `+${formatRupiah(jumlah)}`;
  winPopup.classList.remove("hidden");
  winPopup.classList.add("show");
  playSound(winSound);
}

function closeWinnerPopup() {
  winPopup.classList.add("hidden");
  winPopup.classList.remove("show");
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
  document.getElementById("pesan").innerText = "";
  playSound(spinSound);

  let hasil = [null, null, null];
  let menang = 0;
  let simbolMenangFinal = simbolMenang[Math.floor(Math.random() * simbolMenang.length)];
  let bolehMenang = false;
  let jumlahMenang = 0;

  if (pengaturan.modeOtomatis) {
    bolehMenang = Math.random() * 100 < pengaturan.persentaseMenang;
    jumlahMenang = Math.floor(pengaturan.minMenang + Math.random() * (pengaturan.maxMenang - pengaturan.minMenang));
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
    saldo += menang;
    tampilkanSaldo();
    showWinnerPopup(menang);
  } else {
    document.getElementById("pesan").innerText = `😢 Kalah!`;
  }

  isSpinning = false;
  spinBtn.disabled = false;
  spinBtn.style.opacity = 1;
}

document.addEventListener("DOMContentLoaded", () => {
  saldo = 500000; // saldo awal dummy
  tampilkanSaldo();
});
