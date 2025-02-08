import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from Env import DATABASE_URL

class Store:
    def __init__(self):
        self.conn = psycopg2.connect(DATABASE_URL)
        self._init_tables()
    
    def _init_tables(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS conversations (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    vocabulary_used TEXT
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    conversation_id INTEGER REFERENCES conversations(id),
                    content TEXT NOT NULL,
                    is_user BOOLEAN DEFAULT TRUE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS speech_records (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    text TEXT NOT NULL,
                    confidence_score FLOAT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            self.conn.commit()

    def get_or_create_user(self, username: str, email: str) -> int:
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT id FROM users WHERE username = %s LIMIT 1", (username,))
            user = cur.fetchone()
            if not user:
                cur.execute("""
                    INSERT INTO users (username, email)
                    VALUES (%s, %s)
                    RETURNING id
                """, (username, email))
                user = cur.fetchone()
            self.conn.commit()
            return user['id']

    def start_conversation(self, user_id: int, vocabulary: list[str]) -> int:
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO conversations (user_id, vocabulary_used, start_time)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (user_id, ','.join(vocabulary), datetime.now(timezone.utc)))
            conversation_id = cur.fetchone()[0]
            self.conn.commit()
            return conversation_id

    def end_conversation(self, conversation_id: int):
        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE conversations 
                SET end_time = %s 
                WHERE id = %s
            """, (datetime.now(timezone.utc), conversation_id))
            self.conn.commit()

    def save_message(self, conversation_id: int, content: str, is_user: bool):
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO messages (conversation_id, content, is_user, timestamp)
                VALUES (%s, %s, %s, %s)
            """, (conversation_id, content, is_user, datetime.now(timezone.utc)))
            self.conn.commit()

    def save_speech_record(self, user_id: int, text: str, confidence_score: float):
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO speech_records (user_id, text, confidence_score)
                VALUES (%s, %s, %s)
            """, (user_id, text, confidence_score))
            self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()

    def __del__(self):
        self.close() 