import os
import json
import random
from datetime import datetime
from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'rahasia_kuat_dan_lebih_aman')  # Change this in production
app.config['SESSION_COOKIE_SECURE'] = True  # Only send cookies over HTTPS
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour session lifetime

# Constants
TARGET_KEMENANGAN = 5000000
DEFAULT_SALDO = 100000
DEFAULT_PENGATURAN = {
    "modeOtomatis": True,
    "persentaseMenang": 20,
    "minMenang": 50000,
    "maxMenang": 100000
}

# File paths
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
USERS_FILE = os.path.join(DATA_DIR, "users.json")
DATA_FILE = os.path.join(DATA_DIR, "game_stats.txt")
PENGATURAN_FILE = os.path.join(DATA_DIR, "pengaturan.json")

# === Helper Functions ===
def init_files():
    """Initialize data files with default content"""
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump({}, f)

    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            f.write("menang=0\nkalah=0\n")

    if not os.path.exists(PENGATURAN_FILE):
        with open(PENGATURAN_FILE, "w") as f:
            json.dump(DEFAULT_PENGATURAN, f)

def read_users():
    """Read users data with error handling"""
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def write_users(users):
    """Write users data atomically"""
    temp_file = USERS_FILE + ".tmp"
    with open(temp_file, "w") as f:
        json.dump(users, f, indent=2)
    os.replace(temp_file, USERS_FILE)

def read_data():
    """Read game statistics"""
    try:
        with open(DATA_FILE, "r") as f:
            lines = f.readlines()
        return {k: int(v) for line in lines if "=" in line for k, v in [line.strip().split("=")]}
    except (FileNotFoundError, ValueError):
        return {"menang": 0, "kalah": 0}

def write_data(data):
    """Write game statistics"""
    temp_file = DATA_FILE + ".tmp"
    with open(temp_file, "w") as f:
        for k, v in data.items():
            f.write(f"{k}={v}\n")
    os.replace(temp_file, DATA_FILE)

def read_pengaturan():
    """Read game settings"""
    try:
        with open(PENGATURAN_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return DEFAULT_PENGATURAN.copy()

def write_pengaturan(data):
    """Write game settings"""
    temp_file = PENGATURAN_FILE + ".tmp"
    with open(temp_file, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(temp_file, PENGATURAN_FILE)

def login_required(f):
    """Decorator to ensure user is logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# Initialize data files
init_files()

# === Authentication Routes ===
@app.route("/", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for("game"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            return render_template("login.html", error="Username dan password harus diisi")

        users = read_users()
        if username not in users or not check_password_hash(users[username]["password"], password):
            return render_template("login.html", error="Username atau password salah")

        session["username"] = username
        return redirect(url_for("game"))

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not password:
            return render_template("register.html", error="Username dan password harus diisi")

        if password != confirm_password:
            return render_template("register.html", error="Konfirmasi password tidak cocok")

        users = read_users()
        if username in users:
            return render_template("register.html", error="Username sudah digunakan")

        users[username] = {
            "password": generate_password_hash(password),
            "saldo": DEFAULT_SALDO,
            "created_at": datetime.now().isoformat()
        }
        write_users(users)

        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

# === Game Pages ===
@app.route("/game")
@login_required
def game():
    return render_template("game.html")

@app.route("/admin")
@login_required
def admin():
    return render_template("admin.html")

# === API Routes ===
@app.route("/api/pengaturan", methods=["GET", "POST"])
@login_required
def pengaturan():
    if request.method == "GET":
        return jsonify(read_pengaturan())
    
    try:
        new_settings = request.get_json()
        current_settings = read_pengaturan()
        
        # Validate and update settings
        validated_settings = {
            "modeOtomatis": bool(new_settings.get("modeOtomatis", current_settings["modeOtomatis"])),
            "persentaseMenang": max(0, min(100, int(new_settings.get("persentaseMenang", current_settings["persentaseMenang"]))),
            "minMenang": max(0, int(new_settings.get("minMenang", current_settings["minMenang"]))),
            "maxMenang": max(0, int(new_settings.get("maxMenang", current_settings["maxMenang"])))
        }
        
        write_pengaturan(validated_settings)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/should_win")
@login_required
def should_win():
    pengaturan = read_pengaturan()
    data = read_data()

    response = {"bolehMenang": False, "jumlahMenang": 0}
    
    if data["menang"] < TARGET_KEMENANGAN:
        chance = random.randint(1, 100)
        if chance <= pengaturan["persentaseMenang"]:
            response["bolehMenang"] = True
            response["jumlahMenang"] = random.randint(
                pengaturan["minMenang"],
                pengaturan["maxMenang"]
            )
    
    return jsonify(response)

@app.route("/api/log", methods=["POST"])
@login_required
def log_spin():
    try:
        data = request.get_json()
        status = data.get("status")
        jumlah = int(data.get("jumlah", 0))
        
        game_stats = read_data()
        
        if status == "MENANG":
            game_stats["menang"] += jumlah
        elif status == "KALAH":
            game_stats["kalah"] += jumlah
        
        write_data(game_stats)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/status")
@login_required
def status():
    data = read_data()
    total = data["menang"] + data["kalah"]
    winrate = (data["menang"] / total * 100) if total > 0 else 0
    
    return jsonify({
        "menang": data["menang"],
        "kalah": data["kalah"],
        "winrate": round(winrate, 2),
        "targetTercapai": data["menang"] >= TARGET_KEMENANGAN
    })

@app.route("/api/saldo")
@login_required
def api_saldo():
    users = read_users()
    username = session["username"]
    return jsonify({"saldo": users.get(username, {}).get("saldo", DEFAULT_SALDO)})

@app.route("/api/update_saldo", methods=["POST"])
@login_required
def update_saldo():
    try:
        new_saldo = int(request.json.get("saldo", 0))
        username = session["username"]
        
        users = read_users()
        if username not in users:
            return jsonify({"success": False, "error": "User not found"}), 404
            
        users[username]["saldo"] = new_saldo
        write_users(users)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

# Debug route (remove in production)
@app.route("/debug/users")
def debug_users():
    users = read_users()
    return jsonify(users)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
