import psycopg2
from psycopg2.extras import DictCursor
from psycopg2.pool import SimpleConnectionPool
from datetime import datetime, timezone
from typing import List
import time

from Env import DATABASE_URL

class Store:
    _instance = None
    _pool = None
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Store, cls).__new__(cls)
            cls._instance._create_pool()
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._init_tables()

    def _create_pool(self):
        """Create the connection pool with retries."""
        for attempt in range(self.MAX_RETRIES):
            try:
                self._pool = SimpleConnectionPool(
                    minconn=1, 
                    maxconn=20, 
                    dsn=DATABASE_URL
                )
                if self._pool:
                    return
            except psycopg2.Error as e:
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
                    continue
                raise Exception(f"Failed to create connection pool after {self.MAX_RETRIES} attempts: {str(e)}")

    def _get_conn(self):
        """Get a connection from the pool with retry logic."""
        if not self._pool:
            self._create_pool()
        
        for attempt in range(self.MAX_RETRIES):
            try:
                conn = self._pool.getconn()
                if conn:
                    # Test the connection
                    with conn.cursor() as cur:
                        cur.execute('SELECT 1')
                    return conn
            except psycopg2.Error:
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
                    # Try to recreate the pool
                    self._create_pool()
                    continue
        raise Exception("Failed to get a valid database connection")

    def _put_conn(self, conn):
        """Return a connection to the pool."""
        if self._pool and conn:
            self._pool.putconn(conn)

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
                        language_level VARCHAR(20) DEFAULT '1',
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
                """)
                conn.commit()
        except psycopg2.Error as e:
            conn.rollback()
            raise Exception(f"Failed to initialize tables: {str(e)}")
        finally:
            self._put_conn(conn)

    def get_or_create_user(self, username: str, email: str, language_level: str = '1') -> int:
        """Return user ID, creating a user record if it doesn't exist."""
        conn = self._get_conn()
        try:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("SELECT id FROM users WHERE username = %s LIMIT 1", (username,))
                user = cur.fetchone()
                if not user:
                    cur.execute("""
                        INSERT INTO users (username, email, language_level)
                        VALUES (%s, %s, %s)
                        RETURNING id
                    """, (username, email, language_level))
                    user = cur.fetchone()
                    conn.commit()
                return user['id']
        except psycopg2.Error as e:
            conn.rollback()
            raise Exception(f"Error in get_or_create_user: {str(e)}")
        finally:
            self._put_conn(conn)

    def update_language_level(self, user_id: int, new_level: str) -> None:
        """Update user's language level."""
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users
                    SET language_level = %s
                    WHERE id = %s
                """, (new_level, user_id))
                conn.commit()
        except psycopg2.Error as e:
            conn.rollback()
            raise Exception(f"Error in update_language_level: {str(e)}")
        finally:
            self._put_conn(conn)

    def get_language_level(self, user_id: int) -> str:
        """Get user's current language level."""
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT language_level
                    FROM users
                    WHERE id = %s
                """, (user_id,))
                result = cur.fetchone()
                return result[0] if result else '1'
        except psycopg2.Error as e:
            raise Exception(f"Error in get_language_level: {str(e)}")
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
        try:
            if self._pool:
                self._pool.closeall()
                self._pool = None
        except Exception:
            pass  # Silently handle any closure errors

    def __del__(self):
        try:
            if hasattr(self, '_pool') and self._pool:
                self.close()
        except Exception:
            pass  # Silently handle any cleanup errors