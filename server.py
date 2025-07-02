import os
import json
import random
from datetime import datetime
from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    PERMANENT_SESSION_LIFETIME=3600
)

# File paths
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
USERS_FILE = os.path.join(DATA_DIR, "users.json")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

# Initialize data files
def init_files():
    defaults = [
        (USERS_FILE, {}),
        (STATS_FILE, {"total_spins": 0, "wins": 0, "losses": 0}),
        (CONFIG_FILE, {
            "min_bet": 1000,
            "max_bet": 100000,
            "win_rate": 30,
            "min_win": 5000,
            "max_win": 50000
        })
    ]
    
    for file_path, default in defaults:
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump(default, f)

def load_data(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_data(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

# Initialize data files
init_files()

@app.route('/', methods=['GET'])
def home():
    if 'username' in session:
        return redirect(url_for('game'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'username' in session:
            return redirect(url_for('game'))
        return render_template('login.html')
    
    users = load_data(USERS_FILE)
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    
    if not username or not password:
        return render_template('login.html', error='Username and password required')
    
    if username not in users or not check_password_hash(users[username]['password'], password):
        return render_template('login.html', error='Invalid credentials')
    
    session['username'] = username
    return redirect(url_for('game'))

@app.route('/game', methods=['GET'])
@login_required
def game():
    users = load_data(USERS_FILE)
    username = session['username']
    return render_template('game.html', username=username, balance=users[username]['saldo'])

# API ENDPOINTS
@app.route('/api/user', methods=['GET', 'POST'])
@login_required
def user_api():
    users = load_data(USERS_FILE)
    username = session['username']
    
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
            data = request.get_json()
            users[username]['saldo'] = int(data.get('saldo', users[username]['saldo']))
            users[username]['last_update'] = datetime.now().isoformat()
            save_data(USERS_FILE, users)
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        # Tampilkan form register
        return render_template('register.html')
    
    # Handle POST request (submit form)
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')

    # Validasi input
    if not username or not password:
        return render_template('register.html', error='Username dan password harus diisi')

    if password != confirm_password:
        return render_template('register.html', error='Password tidak cocok')

    users = load_data(USERS_FILE)
    if username in users:
        return render_template('register.html', error='Username sudah digunakan')

    # Buat user baru
    users[username] = {
        'password': generate_password_hash(password),
        'saldo': 100000,
        'created_at': datetime.now().isoformat()
    }
    save_data(USERS_FILE, users)
    
    # Redirect ke login setelah registrasi berhasil
    return redirect(url_for('login'))
    
@app.route('/api/spin', methods=['POST'])
@login_required
def spin():
    try:
        users = load_data(USERS_FILE)
        stats = load_data(STATS_FILE)
        config = load_data(CONFIG_FILE)
        username = session['username']
        
        # Validate request
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
            
        data = request.get_json()
        bet = int(data.get('bet', 0))
        
        # Validate bet
        if bet < config['min_bet']:
            return jsonify({"error": f"Minimum bet is {config['min_bet']}"}), 400
        if bet > config['max_bet']:
            return jsonify({"error": f"Maximum bet is {config['max_bet']}"}), 400
        if bet > users[username]['saldo']:
            return jsonify({"error": "Insufficient balance"}), 400
        
        # Process spin
        users[username]['saldo'] -= bet
        stats['total_spins'] += 1
        
        # Check win
        if random.randint(1, 100) <= config['win_rate']:
            win_amount = random.randint(config['min_win'], config['max_win'])
            users[username]['saldo'] += win_amount
            stats['wins'] += 1
            result = {"win": True, "amount": win_amount}
        else:
            stats['losses'] += 1
            result = {"win": False, "amount": 0}
        
        # Save data
        users[username]['last_update'] = datetime.now().isoformat()
        save_data(USERS_FILE, users)
        save_data(STATS_FILE, stats)
        
        return jsonify({
            "success": True,
            "new_balance": users[username]['saldo'],
            "result": result
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
