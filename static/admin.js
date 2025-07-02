<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Admin Panel Slot</title>
  <style>
    :root {
      --primary: #4a6bff;
      --danger: #e63946;
      --dark: #1a1a2e;
    }
    
    body {
      font-family: Arial, sans-serif;
      background: var(--dark);
      color: white;
      padding: 20px;
    }
    
    .container {
      max-width: 600px;
      margin: 0 auto;
      background: rgba(255,255,255,0.1);
      padding: 20px;
      border-radius: 10px;
    }
    
    h2 {
      color: #4a6bff;
      text-align: center;
      margin-bottom: 20px;
    }
    
    .form-group {
      margin-bottom: 15px;
    }
    
    label {
      display: block;
      margin-bottom: 5px;
    }
    
    input, select {
      width: 100%;
      padding: 10px;
      border-radius: 5px;
      border: 1px solid #444;
      background: rgba(255,255,255,0.1);
      color: white;
    }
    
    button {
      background: var(--primary);
      color: white;
      border: none;
      padding: 10px 15px;
      border-radius: 5px;
      cursor: pointer;
      width: 100%;
      margin-top: 10px;
    }
    
    .status {
      margin-top: 15px;
      padding: 10px;
      border-radius: 5px;
      text-align: center;
    }
    
    .success {
      background: rgba(46, 204, 113, 0.2);
      color: #2ecc71;
    }
    
    .error {
      background: rgba(231, 57, 70, 0.2);
      color: var(--danger);
    }
  </style>
</head>
<body>
  <div class="container">
    <h2>🛠️ Panel Admin Slot</h2>
    
    <div class="form-group">
      <label>Mode Otomatis</label>
      <select id="modeOtomatis">
        <option value="true">Aktif</option>
        <option value="false" selected>Mati</option>
      </select>
    </div>
    
    <div class="form-group">
      <label>Persentase Menang (%)</label>
      <input type="number" id="persentaseMenang" min="0" max="100" value="0">
    </div>
    
    <div class="form-group">
      <label>Minimum Menang (Rp)</label>
      <input type="number" id="minMenang" value="50000">
    </div>
    
    <div class="form-group">
      <label>Maksimum Menang (Rp)</label>
      <input type="number" id="maxMenang" value="30000">
    </div>
    
    <div class="form-group">
      <label>Saldo Default (Rp)</label>
      <input type="number" id="defaultSaldo" value="100000">
    </div>
    
    <button id="saveBtn">💾 Simpan Pengaturan</button>
    
    <div id="statusMsg" class="status"></div>
  </div>

  <script>
    document.addEventListener('DOMContentLoaded', () => {
      // Load settings
      fetch('/api/get_settings')
        .then(res => res.json())
        .then(data => {
          document.getElementById('modeOtomatis').value = data.modeOtomatis;
          document.getElementById('persentaseMenang').value = data.persentaseMenang;
          document.getElementById('minMenang').value = data.minMenang;
          document.getElementById('maxMenang').value = data.maxMenang;
          document.getElementById('defaultSaldo').value = data.defaultSaldo;
        });
      
      // Save settings
      document.getElementById('saveBtn').addEventListener('click', () => {
        const settings = {
          modeOtomatis: document.getElementById('modeOtomatis').value === 'true',
          persentaseMenang: parseInt(document.getElementById('persentaseMenang').value),
          minMenang: parseInt(document.getElementById('minMenang').value),
          maxMenang: parseInt(document.getElementById('maxMenang').value),
          defaultSaldo: parseInt(document.getElementById('defaultSaldo').value)
        };
        
        fetch('/api/save_settings', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(settings)
        })
        .then(res => res.json())
        .then(data => {
          const status = document.getElementById('statusMsg');
          status.textContent = 'Pengaturan berhasil disimpan!';
          status.className = 'status success';
          setTimeout(() => status.textContent = '', 3000);
        })
        .catch(err => {
          const status = document.getElementById('statusMsg');
          status.textContent = 'Gagal menyimpan pengaturan';
          status.className = 'status error';
        });
      });
    });
  </script>
</body>
</html>
