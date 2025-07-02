import os
import sqlite3
import random
from datetime import datetime
from flask import Flask, request, jsonify, session, render_template, redirect, url_for, g
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(32)
app.config.update(
    DATABASE=os.path.join(app.instance_path, 'users.db'),
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=86400,  # 1 day in seconds
    UPLOAD_FOLDER='static'
)

# Default settings
DEFAULT_SETTINGS = {
    "mode_otomatis": False,
    "persentase_menang": 0,
    "min_menang": 50000,
    "max_menang": 30000,
    "default_saldo": 100000,
    "min_saldo": 0,
    "max_bet": 500000
}

# Database helper functions
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        
        # Create tables
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                saldo INTEGER DEFAULT 100000,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        db.execute('''
            CREATE TABLE IF NOT EXISTS game_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                menang INTEGER DEFAULT 0,
                kalah INTEGER DEFAULT 0,
                total_spin INTEGER DEFAULT 0
            )
        ''')
        
        db.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mode_otomatis BOOLEAN DEFAULT 0,
                persentase_menang INTEGER DEFAULT 0,
                min_menang INTEGER DEFAULT 50000,
                max_menang INTEGER DEFAULT 30000,
                default_saldo INTEGER DEFAULT 100000,
                min_saldo INTEGER DEFAULT 0,
                max_bet INTEGER DEFAULT 500000
            )
        ''')
        
        # Insert default settings if not exists
        if db.execute('SELECT COUNT(*) FROM settings').fetchone()[0] == 0:
            db.execute('''
                INSERT INTO settings 
                (mode_otomatis, persentase_menang, min_menang, max_menang, default_saldo, min_saldo, max_bet)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                DEFAULT_SETTINGS['mode_otomatis'],
                DEFAULT_SETTINGS['persentase_menang'],
                DEFAULT_SETTINGS['min_menang'],
                DEFAULT_SETTINGS['max_menang'],
                DEFAULT_SETTINGS['default_saldo'],
                DEFAULT_SETTINGS['min_saldo'],
                DEFAULT_SETTINGS['max_bet']
            ))
        
        db.commit()

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

# Initialize database
init_db()

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
    
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')

    if not username or not password:
        return render_template('login.html', error='Username dan password harus diisi')

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

    if user is None or not check_password_hash(user['password'], password):
        return render_template('login.html', error='Username atau password salah')

    session.permanent = True
    session['username'] = username
    return redirect(url_for('game'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    confirm = request.form.get('confirm_password', '')

    if not username or not password:
        return render_template('register.html', error='Username dan password harus diisi')

    if password != confirm:
        return render_template('register.html', error='Konfirmasi password tidak cocok')

    db = get_db()
    
    # Check if username exists
    if db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone():
        return render_template('register.html', error='Username sudah terdaftar')

    # Get default saldo from settings
    settings = db.execute('SELECT default_saldo FROM settings').fetchone()
    default_saldo = settings['default_saldo'] if settings else DEFAULT_SETTINGS['default_saldo']

    # Insert new user
    db.execute(
        'INSERT INTO users (username, password, saldo) VALUES (?, ?, ?)',
        (username, generate_password_hash(password), default_saldo)
    )
    db.commit()
    
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/game')
@login_required
def game():
    return render_template('game.html')

### API Routes ###
@app.route('/api/user', methods=['GET'])
@login_required
def user_data():
    db = get_db()
    user = db.execute('''
        SELECT saldo, last_update 
        FROM users 
        WHERE username = ?
    ''', (session['username'],)).fetchone()
    
    if not user:
        # Create user data if not exists (shouldn't happen)
        settings = db.execute('SELECT default_saldo FROM settings').fetchone()
        default_saldo = settings['default_saldo'] if settings else DEFAULT_SETTINGS['default_saldo']
        
        db.execute('''
            INSERT INTO users (username, password, saldo)
            VALUES (?, ?, ?)
        ''', (session['username'], '', default_saldo))
        db.commit()
        
        return jsonify({
            'saldo': default_saldo,
            'last_update': datetime.now().isoformat()
        })
    
    return jsonify({
        'saldo': user['saldo'],
        'last_update': user['last_update']
    })

@app.route('/api/settings', methods=['GET'])
@login_required
def game_settings():
    db = get_db()
    settings = db.execute('SELECT * FROM settings').fetchone()
    return jsonify(dict(settings)) if settings else jsonify(DEFAULT_SETTINGS)

@app.route('/api/spin', methods=['POST'])
@login_required
def spin():
    try:
        db = get_db()
        
        # Get user data
        user = db.execute('''
            SELECT saldo FROM users WHERE username = ?
        ''', (session['username'],)).fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get settings
        settings = db.execute('SELECT * FROM settings').fetchone()
        if not settings:
            settings = DEFAULT_SETTINGS
        
        # Validate bet
        bet = int(request.json.get('bet', 0))
        if bet <= 0 or bet > user['saldo'] or bet > settings['max_bet']:
            return jsonify({'error': 'Invalid bet amount'}), 400
        
        # Update balance
        new_balance = user['saldo'] - bet
        db.execute('''
            UPDATE users SET saldo = ?, last_update = ?
            WHERE username = ?
        ''', (new_balance, datetime.now().isoformat(), session['username']))
        
        # Check win condition
        win_chance = random.randint(1, 100)
        if win_chance <= settings['persentase_menang']:
            win_amount = random.randint(settings['min_menang'], settings['max_menang'])
            new_balance += win_amount
            db.execute('''
                UPDATE game_stats 
                SET menang = menang + ?, total_spin = total_spin + 1
            ''', (win_amount,))
            result = {'win': True, 'amount': win_amount}
        else:
            db.execute('''
                UPDATE game_stats 
                SET kalah = kalah + ?, total_spin = total_spin + 1
            ''', (bet,))
            result = {'win': False, 'amount': 0}
        
        # Update user balance if won
        if result['win']:
            db.execute('''
                UPDATE users SET saldo = ?, last_update = ?
                WHERE username = ?
            ''', (new_balance, datetime.now().isoformat(), session['username']))
        
        db.commit()
        
        return jsonify({
            'success': True,
            'new_balance': new_balance,
            'result': result
        })
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Register teardown function
app.teardown_appcontext(close_db)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
