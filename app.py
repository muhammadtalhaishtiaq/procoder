from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify
import sqlite3
import os
import uuid
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import json
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
        # db.execute('''
        #     CREATE TABLE IF NOT EXISTS users (
        #         id INTEGER PRIMARY KEY AUTOINCREMENT,
        #         email TEXT UNIQUE,
        #         password TEXT
        #     )
        # ''')
        # db.execute('''
        #     CREATE TABLE IF NOT EXISTS sessions (
        #         id INTEGER PRIMARY KEY AUTOINCREMENT,
        #         session_id TEXT,
        #         current_code TEXT,
        #         instructions TEXT,
        #         user_id INTEGER,
        #         timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        #     )
        # ''')
        # db.commit()


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
    
    # db = get_db()
    # sessions= db.execute(
    #     'SELECT * FROM sessions WHERE user_id = ? AND session_id = ?',
    #     (session['user_id'], session['session_id'])
    # ).fetchone()
    
    # #get all sessions of thi suser
    # all_sessions = db.execute(
    #     'SELECT * FROM sessions WHERE user_id = ? and current_code is not null ORDER BY timestamp DESC',
    #     (session['user_id'],)
    # ).fetchall()
    sessions= []
    all_sessions= []

    # if(sessions):
    return render_template('home.html', session=session)
    # else:
        # return redirect('login')
    
# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    #first we will check if user id and session is already exists
    current_session = get_current_session()
    print('current_session: ', current_session)
    if not current_session:
        print('current_session is not exists')
        if request.method == 'POST':
            print('request.method is POST')
            email = request.form['email']
            password = request.form['password']
            print('email: ', email)
            print('password: ', password)
            
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
        return render_template('auth/login.html', error='', sessions=current_session)
    return redirect(url_for('home'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    # current_session = get_current_session()
    current_session = []
    print('current_session: ', current_session)
    if not current_session:
        print('current_session is not exists')
        if request.method == 'POST':
            print('request.method is POST')
            email = request.form['email']
            name = request.form['user_name']
            password = generate_password_hash(request.form['password'])
            print('email: ', email)
            print('name: ', name)
            print('password: ', password)
            db = get_db()
            try:
                #get user data after insertion
                # user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
                # print('User: ', user)
                #get user data after insertion in one query
                user = db.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?) RETURNING *', (name, email, password)).fetchone()
                print('User: ', user)
                db.commit()
                print('User registered successfully')
                #save user in session and redirect to home page
                session['user_id'] = user['id']
                # session['session_id'] = session_id
                return redirect(url_for('home'))
                # return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                print('Email already exists!')
                return render_template('auth/register.html', error='Email already exists!')
        return render_template('auth/register.html', error='', sessions=current_session)
    return redirect(url_for('home'))
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Session management
def get_current_session(session_id= None, user_id= None):
    # #first we will check if session object exists or not 
    # if not session:
    #     return None
    # session_id = (session.get('session_id') or session_id)
    # user_id = (session.get('user_id') or user_id)
    # print('user_id: ', user_id)
    # print('session_id: ', session_id)

    # if 'user_id' not in session or 'session_id' not in session:
    #     return None
    # db = get_db()
    # session = db.execute(   
    #     'SELECT * FROM sessions WHERE user_id = ? AND session_id = ?',
    #     (user_id, session_id)
    # ).fetchone()
    # print('session: ', session)
    # return session
    return []

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
    print('session: ', session)
    if 'user_id' not in session:
        #save user prompt in session so that after redierting we will use that and generate response from it. 
        if request.json.get('prompt'):
            session['user_prompt'] = request.json.get('prompt')
        return jsonify({'error': 'unauthorized'}), 401
    
    # try:
    #get prompt from session if exists other wise get from request
    # prompt = session.get('user_prompt')
    # if not prompt:
    prompt = request.json.get('prompt')
    print('prompt: ', prompt)
    # response = requests.post(
    #     'https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
    #     headers={'Authorization': f'Bearer {os.getenv("QWEN_API_KEY")}'},
    #     json={
    #         "model": "qwen-max",
    #         "input": {
    #             "messages": [{
    #                 "role": "user",
    #                 "content": f"Generate complete code with instructions. User request: {prompt}\n\nFORMAT:\nCODE:\n{{code}}\nINSTRUCTIONS:\n{{instructions}}"

    #                 }]
    #         }
    #     }
    # )
    starter_prompt = f"""
            Analyze the following user request and categorize it into one of the following types:

            1. **Software Development**: Generate a basic code or Generate a complete code project with files, modules, and dependencies.
            2. **Machine Learning / Data Science**: Create an ML project with datasets, models, training scripts, and evaluation.
            3. **Automation / Scripting**: Generate automation scripts such as web scraping, data processing, or workflow automation.
            4. **DevOps / Infrastructure**: Generate deployment configurations, CI/CD pipelines, or containerization scripts.
            5. **Technical Documentation**: Write structured documentation, guides, or API references.
            6. **Presentation Slides**: Generate structured slides for teaching, pitches, or technical explanations.
            7. **General AI Assistance**: Provide a detailed explanation or conceptual guidance on a topic.
            8. **Other**: If the request doesn't fall into the above, classify it as other.

            **User Request:** {prompt}

            **Output Format:** {{ "category": "<One of the categories above>", "reason": "<Why this category was chosen>" }}

            Make sure the category is accurate. If it's unclear, ask clarifying questions instead of assuming.
            """
    # print('starter_prompt: ', starter_prompt)
    response = requests.post(
        'https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
        headers={'Authorization': f'Bearer {os.getenv("QWEN_API_KEY")}'},
            json={
                "model": "qwen-max",
                "input": {
                    "messages": [{
                        "role": "user",
                        "content": starter_prompt
                        # "content": f"""
                        # Analyze the user request carefully and classify it into one of the following categories:
                        # 1. **Generate Code Project** – If the request is about coding, software development, or creating a full project.
                        # 2. **Generate Documentation** – If the user wants explanations, technical documentation, or API docs.
                        # 3. **Generate Presentation Slides** – If the user is asking for a structured explanation in a slide format.
                        # 4. **General AI Assistance** – If the request doesn't fall into the above, classify it as general AI assistance.
                        
                        # **User Request:** {prompt}
                        
                        # Respond ONLY with the category name from the above list without any additional text.
                        # """
                    }]
                }
            }
        )
    # print('response: ', response.json().get("output").get("text"))
    data = response.json()  # Convert response to JSON
    category = json.loads(data['output']['text'].strip('```json\n'))["category"]
    # category = response.json().get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    print('category: ', category)
    if category == "Software Development":
        specific_prompt = specific_prompt = f"""
            You are an expert software architect. Given the following user request, generate a complete project structure, including necessary files and instructions.

            **User Request:** {prompt}

            **Output Format (Ensure JSON format for frontend parsing):**
            {{ "project_name": "<AI-determined based on request>", "description": "<Short description of what the project does>", "tech_stack": "<Identified technologies (e.g., Python Flask, React, Node.js, etc.)>", "files": [ {{ "path": "<File path (AI decides required structure)>", "content": "<Code content>" }} ], "instructions": {{ "setup": "<How to set up the project>", "run": "<How to run the project>", "config": "<Any necessary configuration details>" }} }}

            - AI must determine the required files based on best practices.
            - Ensure modularity, scalability, and maintainability.
            - If a framework is needed (e.g., Django for backend), configure dependencies.
            - Avoid unnecessary files and keep the response **minimal yet complete**.

            Generate the response in **valid JSON format**.
            """
    elif category == "Machine Learning / Data Science":
        specific_prompt = specific_prompt = f"""
            You are an expert in Machine Learning and Data Science. Given the user's request, generate a structured ML project with necessary scripts, datasets, and model training pipelines.

            **User Request:** {prompt}

            **Output Format (Ensure JSON format for frontend parsing):**
            {{ "project_name": "<AI-determined name>", "description": "<Brief description of the ML task>", "tech_stack": "<Identified technologies (e.g., TensorFlow, PyTorch, Scikit-learn, etc.)>", "files": [ {{ "path": "data/dataset.csv", "content": "<If dataset needs to be generated, describe the format>" }} ], "instructions": {{ "data_prep": "<How to prepare datasets>", "training": "<How to train the model>", "evaluation": "<How to evaluate performance>", "deployment": "<How to deploy the model>" }} }}

            Ensure:
            - Datasets are included or referenced.
            - The project follows industry best practices.
            - Scripts are modular and reusable.

            Generate the response in **valid JSON format**.
            """
    elif category == "Automation / Scripting":
        specific_prompt = specific_prompt = f"""
            You are a scripting expert. Generate an automation script based on the user's request.

            **User Request:** {prompt}

            **Output Format:**
            {{ "script_name": "<AI-generated script name>", "description": "<Brief explanation of what the script does>", "language": "<Python, Bash, PowerShell, etc.>", "files": [ {{ "path": "<Filename based on the script's purpose>", "content": "<Script content>" }} ], "instructions": {{ "usage": "<How to use the script>", "dependencies": "<Any required packages>" }} }}

            - Ensure code is efficient and well-commented.
            - Identify the best scripting language for the task.
            - Include setup instructions.

            Generate the response in **valid JSON format**.
            """
    elif category == "DevOps / Infrastructure":
        specific_prompt = specific_prompt = f"""
            You are a DevOps and cloud expert. Generate the necessary configuration files for the following request.

            **User Request:** {prompt}

            **Output Format:**
            {{ "project_name": "<Name based on the deployment purpose>", "description": "<Short overview>", "tech_stack": "<Docker, Kubernetes, Terraform, AWS, etc.>", "files": [ {{ "path": "<AI-generated relevant file path>", "content": "<File content>" }} ], "instructions": {{ "setup": "<How to set up the infrastructure>", "deployment": "<Steps to deploy>", "monitoring": "<Suggested monitoring tools>" }} }}

            Ensure:
            - Configurations are production-ready.
            - Security best practices are followed.
            - Deployment instructions are included.

            Generate the response in **valid JSON format**.
            """
    elif category == "Technical Documentation":
        specific_prompt = specific_prompt = f"""
            You are an expert technical writer. Create structured documentation for the following user request.

            **User Request:** {prompt}

            **Output Format:**
            {{ "title": "<Document Title>", "sections": [ {{ "heading": "<Section Heading>", "content": "<Content>" }} ] }}

            - Use markdown-compatible formatting.
            - Ensure technical accuracy and clarity.
            - Include examples if relevant.

            Generate the response in **valid JSON format**.
            """
    elif category == "Presentation Slides":
        specific_prompt = specific_prompt = f"""
            You are an expert at creating structured presentation slides. Generate a professional slide deck for the following request.

            **User Request:** {prompt}

            **Output Format:**
            {{ "title": "<Presentation Title>", "slides": [ {{ "title": "Slide 1 Title", "content": "<Main content for slide 1>", "image_suggestion": "<Describe an optional image>" }} ] }}

            - Keep content concise and engaging.
            - Follow best practices for visual presentations.

            Generate the response in **valid JSON format**.
            """
    elif category == "General AI Assistance":
        specific_prompt = f"""
            You are an expert in providing detailed explanations and conceptual guidance on a topic.

            **User Request:** {prompt}

            **Output Format:**
            {{ "title": "<Explanation Title>", "content": "<Detailed explanation>" }}
            """
    else: 
        specific_prompt = f"""
            You are an expert in providing detailed explanations and conceptual guidance on a topic.

            **User Request:** {prompt}

            **Output Format:**
            {{ "title": "<Explanation Title>", "content": "<Detailed explanation>" }}
        """

    # Now send the actual API request based on the classification
    final_response = requests.post(
        'https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
        headers={'Authorization': f'Bearer {os.getenv("QWEN_API_KEY")}'},
        json={
            "model": "qwen-max",
            "input": {
                "messages": [{
                    "role": "user",
                    "content": specific_prompt
                }]
            }
        }
    )
    # print('final_response: ', final_response.json())
    
    data = final_response.json()  # Convert response to JSON
    project_details = json.loads(data['output']['text'].strip('```json\n'))
    print('project_details: ', project_details)


    
    #clear session for user prompt
    # session.pop('user_prompt', None)
        
    # full_text = response.json()['output']['text']
    # code = full_text.split("CODE:")[1].split("INSTRUCTIONS:")[0].strip()
    # instructions = full_text.split("INSTRUCTIONS:")[1].strip()
    # print("session['session_id']: ", session['session_id'])
    # db = get_db()
    # db.execute('UPDATE sessions SET current_code = ?, instructions = ? WHERE session_id = ?',
    #     (code, instructions, session['session_id']))
    # db.commit()

    # if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
    #     return jsonify({
    #             'code': clean_code_response(code),
    #             'instructions': instructions
    #     })
            
    # return redirect(url_for('result'),prompt=prompt, code=code, instructions=instructions)
    # return jsonify({'code': code, 'instructions': instructions, 'prompt': prompt})
    return jsonify({'category': category})
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