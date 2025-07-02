import os
import json
import random
from datetime import datetime
from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'rahasia-kuat-123')
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

# Default settings
DEFAULT_CONFIG = {
    "min_bet": 1000,
    "max_bet": 100000,
    "win_rate": 30,
    "min_win": 5000,
    "max_win": 50000
}

# Initialize data files
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump({}, f)

if not os.path.exists(STATS_FILE):
    with open(STATS_FILE, 'w') as f:
        json.dump({"spins": 0, "wins": 0, "losses": 0}, f)

if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(DEFAULT_CONFIG, f)

# Helper functions
def load_data(file):
    try:
        with open(file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_data(file, data):
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
        users = load_data(USERS_FILE)
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users and check_password_hash(users[username]['password'], password):
            session['username'] = username
            return redirect(url_for('game'))
        return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = load_data(USERS_FILE)
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users:
            return render_template('register.html', error="Username exists")
        
        users[username] = {
            "password": generate_password_hash(password),
            "balance": 100000,
            "created_at": datetime.now().isoformat()
        }
        save_data(USERS_FILE, users)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/game')
@login_required
def game():
    users = load_data(USERS_FILE)
    return render_template('game.html', 
                         username=session['username'],
                         balance=users[session['username']]['balance'])

@app.route('/api/spin', methods=['POST'])
@login_required
def spin():
    try:
        users = load_data(USERS_FILE)
        stats = load_data(STATS_FILE)
        config = load_data(CONFIG_FILE)
        username = session['username']
        
        # Validate bet
        bet = int(request.json.get('bet', 0))
        if bet < config['min_bet']:
            return jsonify({"error": f"Minimum bet is {config['min_bet']}"}), 400
        if bet > config['max_bet']:
            return jsonify({"error": f"Maximum bet is {config['max_bet']}"}), 400
        if bet > users[username]['balance']:
            return jsonify({"error": "Insufficient balance"}), 400
        
        # Process spin
        users[username]['balance'] -= bet
        stats['spins'] += 1
        
        # Check win
        if random.randint(1, 100) <= config['win_rate']:
            win_amount = random.randint(config['min_win'], config['max_win'])
            users[username]['balance'] += win_amount
            stats['wins'] += 1
            result = {"status": "win", "amount": win_amount}
        else:
            stats['losses'] += 1
            result = {"status": "lose", "amount": 0}
        
        # Save data
        save_data(USERS_FILE, users)
        save_data(STATS_FILE, stats)
        
        return jsonify({
            "success": True,
            "balance": users[username]['balance'],
            "result": result
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
