import os
import sys
from typing import List

from google import genai

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Env import GEMINI_API_KEY
from Backend.Store import Store

class ChatbotWrapper:
    def __init__(self, api_key: str):
        self.bot = genai.Client(api_key=api_key)
        
    def respond(self, prompt: str):
        response = self.bot.models.generate_content(
            model="gemini-2.0-flash", contents=prompt
        )
        response = response.candidates[0].content.parts[0].text
        response = response.split("：")[-1].split(":")[-1].strip()
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
        self.store = Store() if user_id else None
        self.conversation_id = None
        
        if user_id:
            self.conversation_id = self.store.start_conversation(user_id, vocab)
        
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
        
        self.assess_template = """
        Please summarize the content of this conversation and the pronunciation evaluation indicators, and make a summary of the situation of the student using a friendly tone.
        **Please respond in English**
        {context}
        {metrics}
        """
        
    def respond(self, if_end=False):
        prompt = self.prompt_template.format(vocab='、'.join(self.vocab), context='\n'.join(self.context))
        
        if if_end and self.store and self.conversation_id:
            prompt += self.closing_template
            self.store.end_conversation(self.conversation_id)
        
        response = self.bot.respond(prompt)
        if self.store and self.conversation_id:
            self.store.save_message(self.conversation_id, response, is_user=False)
        
        return response
    
    def assess(self, metrics):
        prompt = self.assess_template.format(context='\n'.join(self.context), metrics=metrics)
        response = self.bot.respond(prompt)
        return response
        
    def converse(self):
        response = self.respond()
        self.context.append(f"老师：{response}")
        print(f"老师：{response}")
        
        for _ in range(self.rounds - 1):
            cur_input = input("学生：")
            if self.store and self.conversation_id:
                self.store.save_message(self.conversation_id, cur_input, is_user=True)
            self.context.append(f"学生：{cur_input}")
            response = self.respond()
            self.context.append(f"老师：{response}")
            print(f"老师：{response}")
            
        cur_input = input("学生：")
        if self.store and self.conversation_id:
            self.store.save_message(self.conversation_id, cur_input, is_user=True)
        self.context.append(f"学生：{cur_input}")
        response = self.respond(if_end=True)
        self.context.append(f"老师：{response}")
        print(f"老师：{response}")
        
    def get_context(self):
        return self.context

    def __del__(self):
        if self.store:
            self.store.close()


if __name__ == "__main__":
    # Test the chatbot
    bot = ChatbotWrapper(api_key=GEMINI_API_KEY)
    store = Store()
    
    # Create a test user
    user_id = store.get_or_create_user('test_user', 'test@example.com')
    store.close()

    # Start conversation with database integration
    c = ChatConversation(bot, 5, ["你好", "再见", "谢谢"], user_id=user_id)
    c.converse()