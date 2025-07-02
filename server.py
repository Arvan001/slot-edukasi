import os
import json
import random
from datetime import datetime
from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'rahasia-slot-game-12345')
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    PERMANENT_SESSION_LIFETIME=3600  # 1 hour
)

# File paths
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
USERS_FILE = os.path.join(DATA_DIR, "users.json")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

# Default game settings
DEFAULT_CONFIG = {
    "min_bet": 1000,
    "max_bet": 100000,
    "win_rate": 30,  # 30% chance to win
    "min_win": 5000,
    "max_win": 50000
}

# Initialize data files
def init_data_files():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)
    if not os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'w') as f:
            json.dump({"total_spins": 0, "wins": 0, "losses": 0}, f)
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f)

# Helper functions
def load_json(file):
    try:
        with open(file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=2)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            return jsonify({"error": "Login required"}), 401
        return f(*args, **kwargs)
    return decorated

# Routes
@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('game'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = load_json(USERS_FILE)
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users and check_password_hash(users[username]['password'], password):
            session['username'] = username
            return redirect(url_for('game'))
        return render_template('login.html', error="Username atau password salah!")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = load_json(USERS_FILE)
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            return render_template('register.html', error="Password tidak cocok!")
        
        if username in users:
            return render_template('register.html', error="Username sudah digunakan!")
        
        users[username] = {
            "password": generate_password_hash(password),
            "saldo": 100000,
            "created_at": datetime.now().isoformat()
        }
        save_json(USERS_FILE, users)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/game')
@login_required
def game():
    users = load_json(USERS_FILE)
    username = session['username']
    return render_template('game.html', username=username, balance=users[username]['saldo'])

# API Endpoints
@app.route('/api/user', methods=['GET', 'POST'])
@login_required
def user_api():
    username = session['username']
    users = load_json(USERS_FILE)
    
    if request.method == 'GET':
        if username not in users:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify({
            "success": True,
            "saldo": users[username]['saldo'],
            "last_update": users[username].get('last_update')
        })
    
    elif request.method == 'POST':
        try:
            new_balance = int(request.json.get('saldo', users[username]['saldo']))
            users[username]['saldo'] = new_balance
            users[username]['last_update'] = datetime.now().isoformat()
            save_json(USERS_FILE, users)
            
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/spin', methods=['POST'])
@login_required
def spin():
    try:
        users = load_json(USERS_FILE)
        stats = load_json(STATS_FILE)
        config = load_json(CONFIG_FILE)
        username = session['username']
        
        # Validasi user
        if username not in users:
            return jsonify({"error": "User not found"}), 404
            
        # Validasi taruhan
        bet = int(request.json.get('bet', 0))
        if bet < config['min_bet']:
            return jsonify({"error": f"Minimum bet: {config['min_bet']}"}), 400
        if bet > config['max_bet']:
            return jsonify({"error": f"Maximum bet: {config['max_bet']}"}), 400
        if bet > users[username]['saldo']:
            return jsonify({"error": "Insufficient balance"}), 400
            
        # Proses putaran
        users[username]['saldo'] -= bet
        stats['total_spins'] += 1
        
        # Logika kemenangan
        if random.randint(1, 100) <= config['win_rate']:
            win_amount = random.randint(config['min_win'], config['max_win'])
            users[username]['saldo'] += win_amount
            stats['wins'] += 1
            result = {"win": True, "amount": win_amount}
        else:
            stats['losses'] += 1
            result = {"win": False, "amount": 0}
            
        # Simpan perubahan
        users[username]['last_update'] = datetime.now().isoformat()
        save_json(USERS_FILE, users)
        save_json(STATS_FILE, stats)
        
        return jsonify({
            "success": True,
            "new_balance": users[username]['saldo'],
            "result": result
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    init_data_files()
    app.run(host='0.0.0.0', port=5000, debug=True)
