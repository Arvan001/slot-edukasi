from flask import Flask, request, jsonify, render_template, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
import random
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)  # More secure random key
app.config['SESSION_COOKIE_SECURE'] = True  # Requires HTTPS in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# File paths
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
DATA_FILE = os.path.join(DATA_DIR, "game_stats.json")
PENGATURAN_FILE = os.path.join(DATA_DIR, "settings.json")
os.makedirs(DATA_DIR, exist_ok=True)

# Constants
TARGET_KEMENANGAN = 5000000
DEFAULT_SETTINGS = {
    "modeOtomatis": False,
    "persentaseMenang": 0,
    "minMenang": 50000,
    "maxMenang": 30000,
    "defaultSaldo": 100000
}

# === Helper Functions ===
def load_json_file(filename, default={}):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def save_json_file(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function

# === Initialize Files ===
if not os.path.exists(USERS_FILE):
    save_json_file(USERS_FILE, {})

if not os.path.exists(DATA_FILE):
    save_json_file(DATA_FILE, {"menang": 0, "kalah": 0})

if not os.path.exists(PENGATURAN_FILE):
    save_json_file(PENGATURAN_FILE, DEFAULT_SETTINGS)

# === Authentication Routes ===
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        users = load_json_file(USERS_FILE)
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        if not username or not password:
            return render_template("login.html", error="Username dan password harus diisi")
        
        if username in users and check_password_hash(users[username]["password"], password):
            session["username"] = username
            return redirect("/game")
        
        return render_template("login.html", error="Username atau password salah")
    
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        users = load_json_file(USERS_FILE)
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        if not username or not password:
            return render_template("register.html", error="Username dan password harus diisi")
        
        if password != confirm_password:
            return render_template("register.html", error="Password tidak cocok")
        
        if username in users:
            return render_template("register.html", error="Username sudah digunakan")
        
        settings = load_json_file(PENGATURAN_FILE, DEFAULT_SETTINGS)
        
        users[username] = {
            "password": generate_password_hash(password),
            "saldo": settings.get("defaultSaldo", 100000)
        }
        save_json_file(USERS_FILE, users)
        return redirect("/")
    
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# === Game Routes ===
@app.route("/game")
@login_required
def game():
    return render_template("game.html")

@app.route("/admin")
@login_required
def admin():
    return render_template("admin.html")

# === API Routes ===
@app.route("/api/settings", methods=["GET", "POST"])
@login_required
def handle_settings():
    if request.method == "GET":
        return jsonify(load_json_file(PENGATURAN_FILE, DEFAULT_SETTINGS))
    else:
        try:
            new_settings = request.get_json()
            # Validate settings
            new_settings["persentaseMenang"] = max(0, min(100, int(new_settings.get("persentaseMenang", 0)))
            new_settings["minMenang"] = max(0, int(new_settings.get("minMenang", 0)))
            new_settings["maxMenang"] = max(0, int(new_settings.get("maxMenang", 0)))
            save_json_file(PENGATURAN_FILE, new_settings)
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/should_win")
@login_required
def should_win():
    settings = load_json_file(PENGATURAN_FILE, DEFAULT_SETTINGS)
    stats = load_json_file(DATA_FILE)
    
    # Check if target already reached
    if stats.get("menang", 0) >= TARGET_KEMENANGAN:
        return jsonify({"bolehMenang": False, "jumlahMenang": 0})
    
    # Check win chance
    if random.randint(1, 100) <= settings.get("persentaseMenang", 0):
        min_win = settings.get("minMenang", 50000)
        max_win = settings.get("maxMenang", 30000)
        return jsonify({
            "bolehMenang": True,
            "jumlahMenang": random.randint(min_win, max_win)
        })
    
    return jsonify({"bolehMenang": False, "jumlahMenang": 0})

@app.route("/api/log", methods=["POST"])
@login_required
def log_spin():
    try:
        data = request.get_json()
        stats = load_json_file(DATA_FILE)
        
        if data.get("status") == "MENANG":
            stats["menang"] += int(data.get("jumlah", 0))
        elif data.get("status") == "KALAH":
            stats["kalah"] += int(data.get("jumlah", 0))
        
        save_json_file(DATA_FILE, stats)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/balance", methods=["GET", "POST"])
@login_required
def handle_balance():
    users = load_json_file(USERS_FILE)
    username = session["username"]
    
    if request.method == "GET":
        return jsonify({"saldo": users.get(username, {}).get("saldo", 0)})
    else:
        try:
            new_balance = int(request.get_json().get("saldo", 0))
            users[username]["saldo"] = new_balance
            save_json_file(USERS_FILE, users)
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/stats")
@login_required
def get_stats():
    stats = load_json_file(DATA_FILE)
    total = stats.get("menang", 0) + stats.get("kalah", 0)
    winrate = (stats.get("menang", 0) / total * 100) if total > 0 else 0
    
    return jsonify({
        "menang": stats.get("menang", 0),
        "kalah": stats.get("kalah", 0),
        "winrate": round(winrate, 2),
        "targetTercapai": stats.get("menang", 0) >= TARGET_KEMENANGAN
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
