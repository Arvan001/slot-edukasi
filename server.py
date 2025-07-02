import os
import json
import random
from datetime import datetime
from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(32)
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=86400  # 1 day in seconds
)

# Configuration
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

USERS_FILE = os.path.join(DATA_DIR, "users.json")
STATS_FILE = os.path.join(DATA_DIR, "game_stats.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

DEFAULT_SETTINGS = {
    "mode_otomatis": False,
    "persentase_menang": 0,
    "min_menang": 50000,
    "max_menang": 30000,
    "default_saldo": 100000,
    "min_saldo": 0,
    "max_bet": 500000
}

# Helper functions
def load_data(filename, default=None):
    """Load JSON data from file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}

def save_data(filename, data):
    """Save data to JSON file"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def init_files():
    """Initialize data files with defaults"""
    if not os.path.exists(USERS_FILE):
        save_data(USERS_FILE, {})
    
    if not os.path.exists(STATS_FILE):
        save_data(STATS_FILE, {"menang": 0, "kalah": 0, "total_spin": 0})
    
    if not os.path.exists(SETTINGS_FILE):
        save_data(SETTINGS_FILE, DEFAULT_SETTINGS)

def validate_settings(settings):
    """Validate and sanitize settings"""
    return {
        "mode_otomatis": bool(settings.get("mode_otomatis", False)),
        "persentase_menang": max(0, min(100, int(settings.get("persentase_menang", 0)))),
        "min_menang": max(0, int(settings.get("min_menang", 50000))),
        "max_menang": max(0, int(settings.get("max_menang", 30000))),
        "default_saldo": max(10000, int(settings.get("default_saldo", 100000))),
        "min_saldo": max(0, int(settings.get("min_saldo", 0))),
        "max_bet": max(1000, int(settings.get("max_bet", 500000)))
    }

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

# Initialize data files
init_files()

### Routes ###
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('game'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'username' in session:
            return redirect(url_for('game'))
        return render_template('login.html')
    
    users = load_data(USERS_FILE, {})
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')

    if not username or not password:
        return render_template('login.html', error='Username dan password harus diisi')

    if username not in users or not check_password_hash(users[username]['password'], password):
        return render_template('login.html', error='Username atau password salah')

    session.permanent = True
    session['username'] = username
    return redirect(url_for('game'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    users = load_data(USERS_FILE, {})
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    confirm = request.form.get('confirm_password', '')

    if not username or not password:
        return render_template('register.html', error='Username dan password harus diisi')

    if password != confirm:
        return render_template('register.html', error='Konfirmasi password tidak cocok')

    if username in users:
        return render_template('register.html', error='Username sudah terdaftar')

    settings = load_data(SETTINGS_FILE, DEFAULT_SETTINGS)
    users[username] = {
        'password': generate_password_hash(password),
        'saldo': settings['default_saldo'],
        'created_at': datetime.now().isoformat(),
        'last_update': datetime.now().isoformat()
    }
    save_data(USERS_FILE, users)
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/game')
@login_required
def game():
    return render_template('game.html')  # You'll need to create this template

### API Routes ###
@app.route('/api/user', methods=['GET', 'POST'])
@login_required
def user_data():
    users = load_data(USERS_FILE)
    username = session['username']
    
    if request.method == 'GET':
        if username not in users:
            settings = load_data(SETTINGS_FILE, DEFAULT_SETTINGS)
            users[username] = {
                'saldo': settings['default_saldo'],
                'last_update': datetime.now().isoformat()
            }
            save_data(USERS_FILE, users)
        
        return jsonify({
            'saldo': users[username]['saldo'],
            'last_update': users[username].get('last_update')
        })
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            users[username]['saldo'] = int(data.get('saldo', users[username]['saldo']))
            users[username]['last_update'] = datetime.now().isoformat()
            save_data(USERS_FILE, users)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/settings', methods=['GET', 'POST'])
@login_required
def game_settings():
    if request.method == 'GET':
        return jsonify(load_data(SETTINGS_FILE, DEFAULT_SETTINGS))
    
    try:
        new_settings = validate_settings(request.get_json())
        save_data(SETTINGS_FILE, new_settings)
        return jsonify({'success': True, 'settings': new_settings})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/spin', methods=['POST'])
@login_required
def spin():
    try:
        users = load_data(USERS_FILE)
        stats = load_data(STATS_FILE, {"menang": 0, "kalah": 0, "total_spin": 0})
        settings = load_data(SETTINGS_FILE, DEFAULT_SETTINGS)
        username = session['username']
        
        # Validate bet
        bet = int(request.json.get('bet', 0))
        if bet <= 0 or bet > users[username]['saldo'] or bet > settings['max_bet']:
            return jsonify({'error': 'Invalid bet amount'}), 400
        
        # Update balance
        users[username]['saldo'] -= bet
        stats['total_spin'] += 1
        
        # Check win condition
        win_chance = random.randint(1, 100)
        if win_chance <= settings['persentase_menang']:
            win_amount = random.randint(settings['min_menang'], settings['max_menang'])
            users[username]['saldo'] += win_amount
            stats['menang'] += win_amount
            result = {'win': True, 'amount': win_amount}
        else:
            stats['kalah'] += bet
            result = {'win': False, 'amount': 0}
        
        # Save updates
        users[username]['last_update'] = datetime.now().isoformat()
        save_data(USERS_FILE, users)
        save_data(STATS_FILE, stats)
        
        return jsonify({
            'success': True,
            'new_balance': users[username]['saldo'],
            'result': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
