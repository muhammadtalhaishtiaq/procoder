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


#Home
@app.route('/')
def home():
    print('Inside home page')
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    print('sessions obect : ', session['user_id'])
    # db = get_db()
    # sessions = db.execute(
    #     'SELECT * FROM sessions WHERE user_id = ? ORDER BY timestamp DESC',
    #     (session['user_id'],)
    # ).fetchall()
    
    db = get_db()
    sessions= db.execute(
        'SELECT * FROM sessions WHERE user_id = ? AND session_id = ?',
        (session['user_id'], session['session_id'])
    ).fetchone()
    
    #get all sessions of thi suser
    all_sessions = db.execute(
        'SELECT * FROM sessions WHERE user_id = ? and current_code is not null ORDER BY timestamp DESC',
        (session['user_id'],)
    ).fetchall()

    if(sessions):
        return render_template('home.html', sessions=sessions, all_sessions=all_sessions)
    else:
        return redirect('login')
    
# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    #first we will check if user id and session is already exists
    current_session = get_current_session()
    if not current_session:
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            
            #fetch from DB
            db = get_db()
            user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            print('User: ', user)
            if user and check_password_hash(user['password'], password):
                print('User found!')
                session['user_id'] = user['id']
                #create new session in DB
                session_id = str(uuid.uuid4())
                db.execute('INSERT INTO sessions (session_id, user_id) VALUES (?, ?)', (session_id, user['id']))
                db.commit()
                session['session_id'] = session_id
                #we will go to / route, on home screen
                return redirect(url_for('home'))
            return render_template('auth/login.html', error='Invalid email or password')
        return render_template('auth/login.html')
    return redirect(url_for('home'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    current_session = get_current_session()
    if not current_session:
        if request.method == 'POST':
            email = request.form['email']
            name = request.form['user_name']
            password = generate_password_hash(request.form['password'])
            db = get_db()
            try:
                db.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', (name, email, password))
                db.commit()
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                return render_template('auth/register.html', error='Email already exists!')
        return render_template('auth/register.html')
    return redirect(url_for('home'))
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Session management
def get_current_session(session_id= None, user_id= None):
    session_id = (session.get('session_id') or session_id)
    user_id = (session.get('user_id') or user_id)
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
    print("session['session_id']: ", session['session_id'])
    db = get_db()
    db.execute('UPDATE sessions SET current_code = ?, instructions = ? WHERE session_id = ?',
        (code, instructions, session['session_id']))
    db.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
                'code': clean_code_response(code),
                'instructions': instructions
        })
            
    # return redirect(url_for('result'),prompt=prompt, code=code, instructions=instructions)
    return jsonify({'code': code, 'instructions': instructions, 'prompt': prompt})
        
    # except Exception as e:
    #     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
    #         return jsonify({'error': str(e)}), 500
    #     raise e

def clean_code_response(response: str) -> str:
    """
    Removes the first line (```language) and last line (```) 
    from a code block response.
    """
    lines = response.strip().split('\n')
    
    # Remove first line if it starts with ```
    if lines and lines[0].strip().startswith('```'):
        lines = lines[1:]
        
    # Remove last line if it's just ```
    if lines and lines[-1].strip() == '```':
        lines = lines[:-1]
        
    return '\n'.join(lines).strip()

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
    current_session = get_current_session()
    print('current_session: ', current_session)
    if not current_session:
        return redirect(url_for('home'))
    # return render_template('result.html')
    return render_template('result.html',
        code=current_session['current_code'],
        instructions=current_session['instructions'],
        sessions=current_session
    )
    
    
def convert_to_bold(text):
    """
    This function takes a string and replaces '**' before and after a word with HTML bold tags '<b>' and '</b>'.
    
    :param text: str, input string containing '**' around the text to be converted to bold
    :return: str, modified string with bold HTML tags
    """
    # Replace '**' at the start and end with '<b>' and '</b>'
    if text.startswith('**') and text.endswith('**'):
        return f"<b>{text[2:-2]}</b>"
    else:
        return text
@app.route('/generated_results/<session_id>')
def get_generated_results( session_id ):
    
    db = get_db()
    chat_session=  db.execute(
            'SELECT * FROM sessions WHERE session_id = "'+ session_id+'" and current_code is not null',
        ).fetchone()
    print('current_chat_session: ', chat_session)
    current_session = get_current_session()
    # print('current_session: ', current_session)
    if not current_session:
        return redirect(url_for('home'))
    # # return render_template('result.html')
    return render_template('result.html',
        code=clean_code_response(chat_session['current_code']),
        instructions=convert_to_bold(chat_session['instructions']),
        sessions=current_session
    )

if __name__ == '__main__':
    init_db()
    app.run(debug=True)