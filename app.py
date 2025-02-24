from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify
import sqlite3
import os
import uuid
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
DATABASE = 'coder.db'

# Database setup
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                password TEXT
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                current_code TEXT,
                instructions TEXT,
                user_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()

# Authentication routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        db = get_db()
        try:
            db.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, password))
            db.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Email already exists!"
    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            return redirect(url_for('home'))
        return "Invalid credentials"
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Session management
def get_current_session():
    session_id = str(uuid.uuid4())
    user_id = session.get('user_id')
    print('user_id: ', user_id)
    print('session_id: ', session_id)

    if 'user_id' not in session or 'session_id' not in session:
        return None
    db = get_db()
    return db.execute(
        'SELECT * FROM sessions WHERE user_id = ? AND session_id = ?',
        (user_id, session_id)
    ).fetchone()

# Main routes
@app.route('/')
def home():
    # if 'user_id' not in session:
    #     return redirect(url_for('login'))
    
    # db = get_db()
    # sessions = db.execute(
    #     'SELECT * FROM sessions WHERE user_id = ? ORDER BY timestamp DESC',
    #     (session['user_id'],)
    # ).fetchall()
    
    return render_template('home.html')

@app.route('/new_chat')
def new_chat():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    session_id = str(uuid.uuid4())
    db = get_db()
    db.execute(
        'INSERT INTO sessions (session_id, user_id) VALUES (?, ?)',
        (session_id, session['user_id'])
    )
    db.commit()
    session['session_id'] = session_id
    session['current_code'] = ''
    session['instructions'] = ''
    return redirect(url_for('result'))

@app.route('/generate', methods=['POST'])
def generate_code():
    # if 'user_id' not in session:
    #     return redirect(url_for('login'))
    

    #add this in a chat history
    # session_id = str(uuid.uuid4())
    # db = get_db()
    # db.execute(
    #     'INSERT INTO sessions (session_id, user_id) VALUES (?, ?)',
    #     (session_id, session['user_id'])
    # )
    # db.commit()
    
    # try:
    prompt = request.json.get('prompt')
    print('prompt: ', prompt)
    response = requests.post(
        'https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
        headers={'Authorization': f'Bearer {os.getenv("QWEN_API_KEY")}'},
        json={
            "model": "qwen-max",
            "input": {
                "messages": [{
                    "role": "user",
                    "content": f"Generate complete code with instructions. User request: {prompt}\n\nFORMAT:\nCODE:\n{{code}}\nINSTRUCTIONS:\n{{instructions}}"

                    }]
            }
        }
    )
        
    full_text = response.json()['output']['text']
    code = full_text.split("CODE:")[1].split("INSTRUCTIONS:")[0].strip()
    instructions = full_text.split("INSTRUCTIONS:")[1].strip()
        
    # db = get_db()
    # db.execute(
    #         'UPDATE sessions current_code = ?, instructions = ? WHERE session_id = ?',
    #         (code, instructions, session['session_id']) )
    # db.commit()

    # if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
    #     return jsonify({
    #             'code': code,
    #             'instructions': instructions
    #     })
            
    # return redirect(url_for('result'),prompt=prompt, code=code, instructions=instructions)
    return jsonify({'code': code, 'instructions': instructions, 'prompt': prompt})
        
    # except Exception as e:
    #     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
    #         return jsonify({'error': str(e)}), 500
    #     raise e

@app.route('/sessions')
def get_sessions():
    if 'user_id' not in session:
        return ''
    
    db = get_db()
    sessions = db.execute(
        'SELECT * FROM sessions WHERE user_id = ? ORDER BY timestamp DESC',
        (session['user_id'],)
    ).fetchall()
    
    return render_template('_sessions.html', sessions=sessions)

@app.route('/result')
def result():
    # current_session = get_current_session()
    # print('current_session: ', current_session)
    # if not current_session:
    #     return redirect(url_for('home'))
    return render_template('result.html')
    # return render_template('result.html',
    #     code=current_session['current_code'],
    #     instructions=current_session['instructions'],
    # )

if __name__ == '__main__':
    init_db()
    app.run(debug=True)