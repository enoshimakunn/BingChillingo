import psycopg2
from psycopg2.extras import DictCursor
from psycopg2.pool import SimpleConnectionPool
from datetime import datetime, timezone
from typing import List

from Env import DATABASE_URL

class Store:
    def __init__(self):
        # Create a connection pool instead of a single connection
        try:
            self.pool = SimpleConnectionPool(
                minconn=1, 
                maxconn=20, 
                dsn=DATABASE_URL
            )
        except psycopg2.Error as e:
            raise Exception(f"Failed to create connection pool: {str(e)}")

        # Initialize tables
        self._init_tables()
    
    def _get_conn(self):
        """Get a connection from the pool."""
        return self.pool.getconn()

    def _put_conn(self, conn):
        """Return a connection to the pool."""
        self.pool.putconn(conn)

    def _init_tables(self) -> None:
        """Create required tables if they do not exist."""
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
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
                conn.commit()
        except psycopg2.Error as e:
            conn.rollback()
            raise Exception(f"Failed to initialize tables: {str(e)}")
        finally:
            self._put_conn(conn)

    def get_or_create_user(self, username: str, email: str) -> int:
        """Return user ID, creating a user record if it doesn't exist."""
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("SELECT id FROM users WHERE username = %s LIMIT 1", (username,))
                user = cur.fetchone()
                if not user:
                    cur.execute("""
                        INSERT INTO users (username, email)
                        VALUES (%s, %s)
                        RETURNING id
                    """, (username, email))
                    user = cur.fetchone()
                    conn.commit()
                return user['id']
        except psycopg2.Error as e:
            conn.rollback()
            raise Exception(f"Error in get_or_create_user: {str(e)}")
        finally:
            self._put_conn(conn)

    def start_conversation(self, user_id: int, vocabulary: List[str]) -> int:
        """Start a conversation for a given user, returning the conversation ID."""
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO conversations (user_id, vocabulary_used, start_time)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (user_id, ','.join(vocabulary), datetime.now(timezone.utc)))
                conversation_id = cur.fetchone()[0]
                conn.commit()
                return conversation_id
        except psycopg2.Error as e:
            conn.rollback()
            raise Exception(f"Error in start_conversation: {str(e)}")
        finally:
            self._put_conn(conn)

    def end_conversation(self, conversation_id: int) -> None:
        """Mark a conversation as ended by updating the end_time."""
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE conversations 
                    SET end_time = %s
                    WHERE id = %s
                """, (datetime.now(timezone.utc), conversation_id))
                conn.commit()
        except psycopg2.Error as e:
            conn.rollback()
            raise Exception(f"Error in end_conversation: {str(e)}")
        finally:
            self._put_conn(conn)

    def save_message(self, conversation_id: int, content: str, is_user: bool) -> None:
        """Save a message record in the messages table."""
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO messages (conversation_id, content, is_user, timestamp)
                    VALUES (%s, %s, %s, %s)
                """, (conversation_id, content, is_user, datetime.now(timezone.utc)))
                conn.commit()
        except psycopg2.Error as e:
            conn.rollback()
            raise Exception(f"Error in save_message: {str(e)}")
        finally:
            self._put_conn(conn)

    def save_speech_record(self, user_id: int, text: str, confidence_score: float) -> None:
        """Save a speech recognition record."""
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO speech_records (user_id, text, confidence_score)
                    VALUES (%s, %s, %s)
                """, (user_id, text, confidence_score))
                conn.commit()
        except psycopg2.Error as e:
            conn.rollback()
            raise Exception(f"Error in save_speech_record: {str(e)}")
        finally:
            self._put_conn(conn)

    def update_last_login(self, user_id: int) -> None:
        """
        Update the user's last_login timestamp.
        Call this method whenever a user logs in.
        """
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users
                    SET last_login = %s
                    WHERE id = %s
                """, (datetime.now(timezone.utc), user_id))
                conn.commit()
        except psycopg2.Error as e:
            conn.rollback()
            raise Exception(f"Error in update_last_login: {str(e)}")
        finally:
            self._put_conn(conn)

    def close(self) -> None:
        """Close the connection pool."""
        if hasattr(self, 'pool') and self.pool:
            self.pool.closeall()

    def __del__(self):
        self.close()