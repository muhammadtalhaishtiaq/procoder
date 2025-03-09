-- CREATE TABLE users (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     name TEXT NOT NULL,
--     email TEXT UNIQUE NOT NULL,
--     password TEXT NOT NULL
--     timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
-- );

-- CREATE TABLE sessions (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     uuid TEXT UNIQUE NOT NULL,
--     chat_history TEXT NOT NULL,
--     current_code TEXT,
--     instructions TEXT,
--     user_id INTEGER,
--     timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
--     FOREIGN KEY (user_id) REFERENCES users (id)
-- );


-- CREATE TABLE session_conversations (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     user__id TEXT UNIQUE NOT NULL,
--     session_id TEXT UNIQUE NOT NULL,
--     chat_id TEXT UNIQUE NOT NULL,
--     role TEXT NOT NULL,
--     content TEXT,
--     ip_token TEXT,
--     op_token INTEGER,
--     timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
--     FOREIGN KEY (session_id) REFERENCES sessions (id)
--     FOREIGN KEY (user_id) REFERENCES users (id)
-- );



-- Users Table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chats Table: Represents individual chat sessions for each user
CREATE TABLE chats (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',  -- e.g., active, archived
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Chat Messages Table: Stores messages within a chat session
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    chat_id INTEGER NOT NULL,
    sender VARCHAR(50) NOT NULL,         -- e.g., 'user', 'assistant', 'system'
    message_type VARCHAR(50) DEFAULT 'text',  -- e.g., 'text', 'code'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_id) REFERENCES chats(id)
);

-- Code Revisions Table: Tracks code generation and updates for a chat
CREATE TABLE code_revisions (
    id SERIAL PRIMARY KEY,
    chat_id INTEGER NOT NULL,
    revision_number INTEGER NOT NULL,  -- Sequential revision tracking per chat
    code_content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_id) REFERENCES chats(id),
    UNIQUE (chat_id, revision_number)
);