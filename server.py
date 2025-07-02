import os
import json
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key")
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

# File paths
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
USER_FILE = os.path.join(DATA_DIR, "users.json")

# Inisialisasi file jika belum ada
if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w") as f:
        json.dump({}, f)

def load_users():
    with open(USER_FILE) as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=2)

# Login Required decorator
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ------------------ ROUTES ------------------ #

@app.route('/')
@login_required
def index():
    return render_template('slot.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = load_users()
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if username in users and check_password_hash(users[username]['password'], password):
            session['username'] = username
            return jsonify(success=True)
        else:
            return jsonify(success=False, error="Username atau password salah.")
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    users = load_users()
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if username in users:
        return jsonify(success=False, error="Username sudah terdaftar.")

    users[username] = {
        'password': generate_password_hash(password),
        'saldo': 100000  # Saldo awal
    }
    save_users(users)
    return jsonify(success=True)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/user')
def api_user():
    if 'username' not in session:
        return jsonify(success=False, error="Belum login"), 403

    users = load_users()
    user = users.get(session['username'])

    if not user:
        return jsonify(success=False, error="User tidak ditemukan")

    return jsonify(success=True, saldo=user.get('saldo', 0))

@app.route('/api/spin', methods=['POST'])
def api_spin():
    if 'username' not in session:
        return jsonify(success=False, error="Belum login"), 403

    data = request.get_json()
    bet = int(data.get('bet', 0))

    users = load_users()
    user = users.get(session['username'])

    if not user:
        return jsonify(success=False, error="User tidak ditemukan")

    if bet <= 0 or user['saldo'] < bet:
        return jsonify(success=False, error="Saldo tidak mencukupi")

    import random
    win_chance = 0.3
    is_win = random.random() < win_chance

    if is_win:
        win_amount = random.randint(50000, 100000)
        user['saldo'] += (win_amount - bet)
    else:
        win_amount = 0
        user['saldo'] -= bet

    users[session['username']] = user
    save_users(users)

    return jsonify(success=True, new_balance=user['saldo'], result={
        'win': is_win,
        'amount': win_amount
    })

# Untuk debugging
@app.route('/admin/users')
def admin_users():
    return jsonify(load_users())

# ------------------ MAIN ------------------ #
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
