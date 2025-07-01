function ambilPengaturan() {
  fetch("/pengaturan")
    .then(res => res.json())
    .then(data => {
      document.getElementById("modeOtomatis").value = data.modeOtomatis ? "true" : "false";
      document.getElementById("persentaseMenang").value = data.persentaseMenang || 20;
      document.getElementById("minMenang").value = data.minMenang || 50000;
      document.getElementById("maxMenang").value = data.maxMenang || 100000;
    });
}

function simpanPengaturan() {
  const data = {
    modeOtomatis: document.getElementById("modeOtomatis").value === "true",
    persentaseMenang: parseInt(document.getElementById("persentaseMenang").value),
    minMenang: parseInt(document.getElementById("minMenang").value),
    maxMenang: parseInt(document.getElementById("maxMenang").value)
  };

  fetch("/pengaturan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  })
    .then(res => res.json())
    .then(res => {
      if (res.success) {
        document.getElementById("statusMsg").textContent = "✅ Berhasil disimpan!";
      }
    });
}

window.addEventListener("DOMContentLoaded", ambilPengaturan);

