from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify
import sqlite3
import os
import uuid
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import json
from datetime import datetime
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
    
    # Optimized Schema Strategy for bolt.new
    # 1. User Registration & Authentication
    # Users sign up/log in, creating an entry in the users table.
    # Their id is used for chat session tracking.
    # 2. Creating a New Chat Session
    # When a user starts a chat, a record is inserted into chats.
    # The chat is assigned a chat_id and marked as active.
    # 3. Storing User Messages
    # Every user input (e.g., prompts, questions) is stored in chat_messages. 
    # Messages are linked to chat_id and categorized by sender.
    # 4. Handling Code Generation & Revisions
    # The first AI-generated code is stored directly in code_revisions with revision_number = 1.
    # Any further modifications or refinements by the user are stored as new revisions (revision_number increments).


    prompt = request.json.get('prompt')
    print('prompt: ', prompt)
    #lets create a new chat in DB
    #if prompt length is more then 20 characters then we will get just the first 20 characters
    db = get_db()
    db.execute('INSERT INTO chats (user_id, title, status) VALUES (?, ?, ?)', (session['user_id'], prompt[:20], 'active'))
    chat_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
    db.commit()
    
    #new chat id
    print('chat_id: ', chat_id)
    #first we will enter user prompt in DB as a role user message
    db = get_db()
    db.execute('INSERT INTO chat_messages (chat_id, sender, message_type, content) VALUES (?, ?, ?, ?)', (chat_id, 'user', 'text', prompt))
    db.commit()
    
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
    response = requests.post(
        'https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
        headers={'Authorization': f'Bearer {os.getenv("QWEN_API_KEY")}'},
            json={
                "model": "qwen-max",
                "input": {
                    "messages": [{
                        "role": "user",
                        "content": starter_prompt                      
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
            You are an advanced AI assistant and a highly skilled software architect. Your primary task is to generate complete, structured coding projects based on user requests. You must ensure the project includes all necessary files, dependencies, and instructions, following industry best practices.
            <project_requirements>
            - Generate a **fully functional coding project** based on the user's request.
            - AI should **dynamically determine** the required files and folder structure—DO NOT hardcode specific file names unless required by a framework.
            - Use **best practices** in software development to ensure modularity, maintainability, and efficiency.
            - Provide **clear and structured project setup instructions** for users to run the project easily.
            </project_requirements>

            <response_format>
            Return your response **strictly** in the following JSON format for easy frontend rendering:
            {{ "project_name": "<Auto-generated project name based on the request>", "description": "<Brief explanation of what the project does>", "tech_stack": "<Identified technologies (e.g., Python Flask, React, Node.js, etc.)>", "files": [ {{ "path": "<File path determined dynamically>", "content": "<Full file content>" }} ], "instructions": {{ "setup": "<Step-by-step setup guide>", "run": "<How to execute the project>", "config": "<Additional configuration details, if any>" }} }}

            - Ensure **each file is included** with its complete content.
            - Provide a **well-structured file hierarchy** for modular development.
            - **Do not summarize or truncate** file contents—always return the **full** content of each file.
            </response_format>

            <best_practices>
            - Follow **industry standards** for writing clean, maintainable, and efficient code.
            - If a framework is required (e.g., Django, Next.js), ensure the necessary dependencies are installed.
            - For backend projects, provide an API structure with proper routing, authentication, and data handling.
            - For frontend projects, include **component-based architecture** for scalability.
            - For full-stack projects, structure the **frontend, backend, and database layers properly**.
            - Always include a **README.md** file with detailed documentation.
            - Ensure **all dependencies are listed** in the appropriate package manager file (e.g., `package.json`, `requirements.txt`).
            </best_practices>

            <project_scope_handling>
            - If the user request is **too vague**, ask clarifying questions before generating the project.
            - If additional context is needed, intelligently infer based on common best practices.
            - If multiple valid approaches exist, choose the **most commonly accepted** approach.
            </project_scope_handling>

            CRITICAL: **Return the response strictly in valid JSON format without any additional text.** Do not explain anything outside the JSON response.

            **User Request:** {prompt}
            """
    elif category == "Machine Learning / Data Science":
        specific_prompt = specific_prompt = f"""
            You are an expert in Machine Learning and Data Science. Given the user's request, generate a structured ML project with necessary scripts, datasets, and model training pipelines.

            **User Request:** {prompt}

            **Output Format (Ensure JSON format for frontend parsing):**
            {{ "project_name": "<AI-determined name>", "description": "<Brief description of the ML task>", "tech_stack": "<Identified technologies (e.g., TensorFlow, PyTorch, Scikit-learn, etc.)>", "files": [ {{ "path": "data/dataset.csv", "content": "<If dataset needs to be generated, describe the format>", "tech_stack": "<Technologies/frameworks used in this specific file>" }} ], "instructions": {{ "data_prep": "<How to prepare datasets>", "training": "<How to train the model>", "evaluation": "<How to evaluate performance>", "deployment": "<How to deploy the model>" }} }}

            Ensure:
            - Datasets are included or referenced.
            - The project follows industry best practices.
            - Scripts are modular and reusable.
            - Each file specifies its tech stack and dependencies.

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
    
    project_name = project_details.get('project_name')
    description = project_details.get('description')
    tech_stack = project_details.get('tech_stack')
    code = project_details.get('files')
    instructions = project_details.get('instructions')
    
    role= 'assistant'
    message_type= 'text'
    print('project_name: ', project_name)
    print('instructions: ', instructions)
    print('description: ', description)
    print('tech_stack: ', tech_stack)
    print('code: ', code)
    
    #saving in DB
    db = get_db()
    db.execute('INSERT INTO chat_messages (chat_id, sender, message_type, content) VALUES (?, ?, ?, ?)', (chat_id, role, message_type, description))
    chat_message_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
    db.commit()
    
    ## colums for code_revisions table
    # chat_message_id
    # revision_number
    # code_content
    # tech_stack
    # instructions
    
    # Convert code list and other complex objects to JSON strings before saving
    code_json = json.dumps(code) if code else None
    tech_stack_json = json.dumps(tech_stack) if tech_stack else None
    instructions_json = json.dumps(instructions) if instructions else None
    
    #now we will save the code in code_revisions table
    db.execute('INSERT INTO code_revisions (chat_id,chat_message_id, revision_number, code_content, tech_stack, instructions, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)', 
              (chat_id, chat_message_id, 1, code_json, tech_stack_json, instructions_json, datetime.now()))
    db.commit()

    return jsonify({
        'code': code,
        'instructions': instructions,
        'prompt': prompt,
        'project_name': project_name,
        'description': description,
        'tech_stack': tech_stack,
        'chat_message_id': chat_message_id,
        'chat_id': chat_id,
        'session_id': session['session_id'],
        'user_id': session['user_id'],
        'category': category,
        'project_details': project_details,
        'revision_number': 1,
        'error': None
    }, 200)


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

@app.route('/result/<chat_id>')
def result(chat_id):
    # current_session = get_current_session()
    # print('current_session: ', current_session)
    # if not current_session:
    #     return redirect(url_for('home'))
    if 'user_id' not in session:
        return redirect(url_for('login'))
    ##
    # we need to get user chat messages of the current chat used by the chat id in parameter
    #current chat 
    db = get_db()
    current_chat = db.execute(
        'SELECT * FROM chats WHERE id = ?',
        (chat_id,)
    ).fetchone()
    # also all its revisions of the codes #
    chat_messages = db.execute(
        'SELECT * FROM chat_messages WHERE chat_id = ?',
        (chat_id,)
    ).fetchall()
    
    #get all revisions of the codes
    code_revisions = db.execute(
        'SELECT * FROM code_revisions WHERE chat_id = ? ORDER BY revision_number DESC LIMIT 1',
        (chat_id,)
    ).fetchone()
    print('Code Revision: ', code_revisions)
    return render_template('result.html',
        chat_messages=chat_messages,
        code_revisions=code_revisions,
        sessions=session,
        current_chat=current_chat
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