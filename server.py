import os
import sqlite3
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key")
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

# Database
DATABASE = os.path.join("instance", "users.db")

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with open("schema.sql") as f:
            db.executescript(f.read())
        db.commit()

# Auth
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
    return render_template('game.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')

        user = get_db().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return jsonify(success=True)
        else:
            return jsonify(success=False, error="Username atau password salah.")
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = generate_password_hash(data.get('password'))

    db = get_db()
    if db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone():
        return jsonify(success=False, error="Username sudah terdaftar.")
    
    # Ambil saldo default dari settings
    setting = db.execute("SELECT default_saldo FROM settings LIMIT 1").fetchone()
    default_saldo = setting['default_saldo'] if setting else 100000

    db.execute("INSERT INTO users (username, password, saldo) VALUES (?, ?, ?)", 
               (username, password, default_saldo))
    db.commit()
    return jsonify(success=True)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/user')
def api_user():
    if 'username' not in session:
        return jsonify(success=False, error="Belum login"), 403

    db = get_db()
    user = db.execute("SELECT saldo FROM users WHERE username = ?", (session['username'],)).fetchone()
    return jsonify(success=True, saldo=user['saldo'])

@app.route('/api/spin', methods=['POST'])
def api_spin():
    if 'username' not in session:
        return jsonify(success=False, error="Belum login"), 403

    data = request.get_json()
    bet = int(data.get('bet', 0))

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (session['username'],)).fetchone()
    if not user or bet <= 0 or user['saldo'] < bet:
        return jsonify(success=False, error="Saldo tidak mencukupi")

    # Ambil pengaturan menang
    setting = db.execute("SELECT * FROM settings LIMIT 1").fetchone()
    import random
    win = False
    amount = 0

    if setting and setting['mode_otomatis']:
        if random.randint(1, 100) <= setting['persentase_menang']:
            win = True
            amount = random.randint(setting['min_menang'], setting['max_menang'])
    else:
        win = random.random() < 0.3
        amount = random.randint(50000, 100000) if win else 0

    new_saldo = user['saldo'] - bet + amount
    db.execute("UPDATE users SET saldo = ? WHERE username = ?", (new_saldo, session['username']))
    db.commit()

    return jsonify(success=True, new_balance=new_saldo, result={'win': win, 'amount': amount})

@app.route('/api/get_settings')
def get_settings():
    setting = get_db().execute("SELECT * FROM settings LIMIT 1").fetchone()
    return jsonify(dict(setting)) if setting else jsonify(success=False)

@app.route('/api/save_settings', methods=['POST'])
def save_settings():
    data = request.get_json()
    db = get_db()

    # Upsert pengaturan
    db.execute("""
        INSERT INTO settings (id, mode_otomatis, persentase_menang, min_menang, max_menang, default_saldo)
        VALUES (1, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            mode_otomatis=excluded.mode_otomatis,
            persentase_menang=excluded.persentase_menang,
            min_menang=excluded.min_menang,
            max_menang=excluded.max_menang,
            default_saldo=excluded.default_saldo
    """, (
        int(data.get('modeOtomatis', False)),
        int(data.get('persentaseMenang', 0)),
        int(data.get('minMenang', 0)),
        int(data.get('maxMenang', 0)),
        int(data.get('defaultSaldo', 100000))
    ))
    db.commit()
    return jsonify(success=True)

# ------------------ INIT DB ------------------ #
if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True, host='0.0.0.0')
