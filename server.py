from flask import Flask, request, jsonify, render_template, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import os, json, random

app = Flask(__name__)
app.secret_key = "rahasia_kuat"
USERS_FILE = "users.json"
DATA_FILE = "data.txt"
PENGATURAN_FILE = "pengaturan.json"
TARGET_KEMENANGAN = 5000000

# === INISIALISASI FILE ===
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        f.write("menang=0\nkalah=0\n")

if not os.path.exists(PENGATURAN_FILE):
    with open(PENGATURAN_FILE, "w") as f:
        json.dump({
            "modeOtomatis": True,
            "persentaseMenang": 20,
            "minMenang": 50000,
            "maxMenang": 100000
        }, f)

# === UTIL FILE ===
def read_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def write_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def read_data():
    with open(DATA_FILE, "r") as f:
        lines = f.readlines()
    return {k: int(v) for line in lines if "=" in line for k, v in [line.strip().split("=")]}

def write_data(data):
    with open(DATA_FILE, "w") as f:
        for k, v in data.items():
            f.write(f"{k}={v}\n")

def read_pengaturan():
    with open(PENGATURAN_FILE, "r") as f:
        return json.load(f)

def write_pengaturan(data):
    with open(PENGATURAN_FILE, "w") as f:
        json.dump(data, f)

# === AUTH ROUTES ===
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        users = read_users()
        uname = request.form["username"]
        passwd = request.form["password"]
        if uname in users and check_password_hash(users[uname]["password"], passwd):
            session["username"] = uname
            return redirect("/game")
        return "Login gagal!"
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        users = read_users()
        uname = request.form["username"]
        if uname in users:
            return "Username sudah digunakan!"
        users[uname] = {
            "password": generate_password_hash(request.form["password"]),
            "saldo": 100000
        }
        write_users(users)
        return redirect("/")
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/")

@app.route("/game")
def game():
    if "username" not in session:
        return redirect("/")
    return render_template("game.html")

@app.route("/admin")
def admin():
    if "username" not in session:
        return redirect("/")
    return render_template("admin.html")

# === API SALDO ===
@app.route("/api/saldo")
def api_saldo():
    users = read_users()
    return jsonify({"saldo": users[session["username"]]["saldo"]})

@app.route("/api/update_saldo", methods=["POST"])
def update_saldo():
    users = read_users()
    users[session["username"]]["saldo"] = request.json.get("saldo", 0)
    write_users(users)
    return jsonify({"success": True})

# === SISTEM LOG / KEMENANGAN ===
@app.route("/log", methods=["POST"])
def log_spin():
    body = request.json
    status = body.get("status")
    jumlah = int(body.get("jumlah"))
    data = read_data()
    if status == "MENANG":
        data["menang"] += jumlah
    elif status == "KALAH":
        data["kalah"] += jumlah
    write_data(data)
    return jsonify({"success": True})

@app.route("/status")
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

@app.route("/should_win")
def should_win():
    pengaturan = read_pengaturan()
    data = read_data()
    if data["menang"] >= TARGET_KEMENANGAN:
        return jsonify({"bolehMenang": False, "jumlahMenang": 0})

    chance = random.randint(1, 100)
    if chance <= pengaturan.get("persentaseMenang", 20):
        min_menang = pengaturan.get("minMenang", 50000)
        max_menang = pengaturan.get("maxMenang", 100000)
        jumlah = random.randint(min_menang, max_menang)
        return jsonify({"bolehMenang": True, "jumlahMenang": jumlah})
    else:
        return jsonify({"bolehMenang": False, "jumlahMenang": 0})

@app.route("/pengaturan", methods=["GET", "POST"])
def pengaturan():
    if request.method == "GET":
        return jsonify(read_pengaturan())
    else:
        data = request.json
        pengaturan = read_pengaturan()
        pengaturan.update({
            "modeOtomatis": data.get("modeOtomatis", pengaturan.get("modeOtomatis")),
            "persentaseMenang": data.get("persentaseMenang", pengaturan.get("persentaseMenang")),
            "minMenang": data.get("minMenang", pengaturan.get("minMenang")),
            "maxMenang": data.get("maxMenang", pengaturan.get("maxMenang"))
        })
        write_pengaturan(pengaturan)
        return jsonify({"success": True})

# === RUN ===
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
