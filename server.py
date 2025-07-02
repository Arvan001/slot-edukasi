import os
import json
import random
from datetime import datetime
from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from threading import Lock

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default-secret-key-change-me')
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=86400  # 1 day in seconds
)

# Constants
DEFAULT_BALANCE = 100000
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
USERS_FILE = os.path.join(DATA_DIR, "users.json")

# Lock for thread-safe file operations
user_data_lock = Lock()

# === Helper Functions ===
def load_users():
    """Load users data with thread safety"""
    try:
        with user_data_lock:
            if not os.path.exists(USERS_FILE):
                return {}
            
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_users(users):
    """Save users data atomically with thread safety"""
    temp_file = USERS_FILE + '.tmp'
    try:
        with user_data_lock:
            with open(temp_file, 'w') as f:
                json.dump(users, f, indent=2, ensure_ascii=False)
            
            # Atomic file replacement
            os.replace(temp_file, USERS_FILE)
    except Exception as e:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise e

def create_user(username, password, balance=DEFAULT_BALANCE):
    """Create a new user"""
    users = load_users()
    if username in users:
        raise ValueError("Username already exists")
    
    users[username] = {
        "password": generate_password_hash(password),
        "saldo": balance,
        "created_at": datetime.now().isoformat(),
        "last_login": None,
        "last_update": datetime.now().isoformat()
    }
    save_users(users)

def get_user(username):
    """Get user data"""
    users = load_users()
    return users.get(username)

def update_user(username, updates):
    """Update user data"""
    users = load_users()
    if username not in users:
        raise ValueError("User not found")
    
    # Preserve existing data
    users[username].update({
        **updates,
        "last_update": datetime.now().isoformat()
    })
    save_users(users)

def validate_user_credentials(username, password):
    """Validate user login credentials"""
    user = get_user(username)
    if not user:
        return False
    return check_password_hash(user["password"], password)

# === Authentication Decorator ===
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

# === Routes ===
@app.route('/', methods=['GET'])
def home():
    if 'username' in session:
        return redirect(url_for('game'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('game'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            return render_template('login.html', error='Username and password are required')
        
        if validate_user_credentials(username, password):
            session['username'] = username
            # Update last login time
            update_user(username, {"last_login": datetime.now().isoformat()})
            return redirect(url_for('game'))
        
        return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not username or not password:
            return render_template('register.html', error='Username and password are required')
        
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')
        
        try:
            create_user(username, password)
            return redirect(url_for('login'))
        except ValueError as e:
            return render_template('register.html', error=str(e))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/game')
@login_required
def game():
    user = get_user(session['username'])
    if not user:
        session.clear()
        return redirect(url_for('login'))
    return render_template('game.html', username=session['username'], balance=user['saldo'])

# === API Routes ===
@app.route('/api/user', methods=['GET'])
@login_required
def get_user_data():
    username = session['username']
    user = get_user(username)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Don't return password hash
    user_data = {k: v for k, v in user.items() if k != 'password'}
    return jsonify(user_data)

@app.route('/api/user/balance', methods=['GET', 'POST'])
@login_required
def user_balance():
    username = session['username']
    user = get_user(username)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    if request.method == 'GET':
        return jsonify({"balance": user['saldo']})
    
    # POST request to update balance
    try:
        new_balance = int(request.json.get('balance', user['saldo']))
        update_user(username, {"saldo": new_balance})
        return jsonify({"success": True, "new_balance": new_balance})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# === Debug Routes ===
@app.route('/debug/users')
def debug_users():
    users = load_users()
    return jsonify({
        "count": len(users),
        "users": list(users.keys()),
        "current_user": session.get('username')
    })

# === Main ===
if __name__ == '__main__':
    # Create initial users file if not exists
    if not os.path.exists(USERS_FILE):
        save_users({})
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
