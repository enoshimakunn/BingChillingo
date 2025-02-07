import os
import sys
from typing import List
from datetime import datetime
import psycopg2
from psycopg2.extras import DictCursor

from google import genai

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Env import GEMINI_API_KEY, DATABASE_URL


class ChatbotWrapper:
    def __init__(self, api_key: str):
        self.bot = genai.Client(api_key=api_key)
        
    def respond(self, prompt: str):
        response = self.bot.models.generate_content(
            model="gemini-2.0-flash", contents=prompt
        )
        response = response.candidates[0].content.parts[0].text
        response = response.split("：")[-1].strip()
        return response

class ChatConversation:
    def __init__(
        self, 
        chatbot: ChatbotWrapper = ChatbotWrapper(GEMINI_API_KEY),
        rounds: int = 5, 
        vocab: List[str] = [],
        user_id: int = None
    ):
        self.rounds = rounds
        self.bot = chatbot
        self.context = []
        self.vocab = vocab
        self.user_id = user_id
        self.conn = None
        self.conversation_id = None
        
        if user_id:
            self.conn = psycopg2.connect(DATABASE_URL)
            self._start_conversation()
        
        self.prompt_template = """
        现在请你扮演一个中文老师，你的学生是一个刚刚开始学习中文的外国人。
        请使用以下词汇，领导一个简单的多轮对话。
        词汇：{vocab}。
        **请注意，你的回答应该是中文的。**
        **请注意，每次回答需要以"老师："开头。**
        **请注意，除非被要求，不要自己结束对话。**
        **请注意，你需要使用以上词汇自行构筑对话内容，引导学生的学习。**
        {context}
        """
        
        self.closing_template = """
        请你用简短的语言总结并结束这个对话。
        **请注意，你的语气需要有结束感。**
        老师：
        """

    def _start_conversation(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO conversations (user_id, vocabulary_used, start_time)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (self.user_id, ','.join(self.vocab), datetime.utcnow()))
            self.conversation_id = cur.fetchone()[0]
            self.conn.commit()

    def _save_message(self, content: str, is_user: bool):
        if self.conn and self.conversation_id:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO messages (conversation_id, content, is_user, timestamp)
                    VALUES (%s, %s, %s, %s)
                """, (self.conversation_id, content, is_user, datetime.utcnow()))
                self.conn.commit()
        
    def respond(self, if_end=False):
        prompt = self.prompt_template.format(vocab='、'.join(self.vocab), context='\n'.join(self.context))
        
        if if_end:
            prompt += self.closing_template
            if self.conn and self.conversation_id:
                with self.conn.cursor() as cur:
                    cur.execute("""
                        UPDATE conversations 
                        SET end_time = %s 
                        WHERE id = %s
                    """, (datetime.utcnow(), self.conversation_id))
                    self.conn.commit()
        
        response = self.bot.respond(prompt)
        self._save_message(response, is_user=False)
        
        return response
        
    def converse(self):
        response = self.respond()
        self.context.append(f"老师：{response}")
        print(f"老师：{response}")
        
        for _ in range(self.rounds - 1):
            cur_input = input("学生：")
            self._save_message(cur_input, is_user=True)
            self.context.append(f"学生：{cur_input}")
            response = self.respond()
            self.context.append(f"老师：{response}")
            print(f"老师：{response}")
            
        cur_input = input("学生：")
        self._save_message(cur_input, is_user=True)
        self.context.append(f"学生：{cur_input}")
        response = self.respond(if_end=True)
        self.context.append(f"老师：{response}")
        print(f"老师：{response}")
        
    def get_context(self):
        return self.context

    def __del__(self):
        if self.conn:
            self.conn.close()


if __name__ == "__main__":
    # First create tables if they don't exist
    conn = psycopg2.connect(DATABASE_URL)
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
    conn.close()

    # Test the chatbot
    bot = ChatbotWrapper(api_key=GEMINI_API_KEY)
    
    # Create a test user if needed
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT id FROM users WHERE username = 'test_user' LIMIT 1")
        user = cur.fetchone()
        if not user:
            cur.execute("""
                INSERT INTO users (username, email)
                VALUES ('test_user', 'test@example.com')
                RETURNING id
            """)
            user = cur.fetchone()
        user_id = user['id']
    conn.close()

    # Start conversation with database integration
    c = ChatConversation(bot, 5, ["你好", "再见", "谢谢"], user_id=user_id)
    c.converse()