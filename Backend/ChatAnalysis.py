import os
import sys
import pandas as pd
from typing import List, Dict, Tuple

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Backend.Store import Store
from Backend.Chatbot import ChatbotWrapper

class ChatAnalysis:
    def __init__(self):
        self.store = Store()
        self.chatbot = ChatbotWrapper()
        self.word_df = pd.read_csv('Data/word.csv')
        self.char_df = pd.read_csv('Data/char.csv')
        
    def _convert_hsk_to_number(self, hsk_level: str) -> str:
        """将 HSK 格式转换为数字格式"""
        if hsk_level.startswith('HSK'):
            return hsk_level[-1]
        return hsk_level
    
    def _convert_number_to_hsk(self, number_level: str) -> str:
        """将数字格式转换为 HSK 格式"""
        return f"HSK{number_level}"
        
    def get_user_level(self, user_id: int) -> str:
        """从数据库获取用户当前级别"""
        level = self.store.get_language_level(user_id)
        return level
    
    def get_words_by_level(self, level: str) -> List[str]:
        """根据级别获取对应的词汇列表"""
        hsk_level = self._convert_number_to_hsk(level)
        words = self.word_df[self.word_df['level'] == hsk_level]['word'].tolist()
        return words
    
    def get_chars_by_level(self, level: str) -> List[str]:
        """根据级别获取对应的汉字列表"""
        hsk_level = self._convert_number_to_hsk(level)
        chars = self.char_df[self.char_df['level'] == hsk_level]['character'].tolist()
        return chars
    
    def assess_user_level(self, user_id: int) -> Tuple[str, float]:
        """评估用户的中文水平
        返回: (建议级别, 置信度)
        """
        current_level = self.get_user_level(user_id)
        
        # start the assessment conversation
        initial_prompt = f"""
        我是一个中文老师，我需要评估你的中文水平。我会问你几个问题，请用中文回答。
        我会根据你的回答中的词汇使用、语法正确性、表达流畅度来评估你的水平。
        
        第一个问题：你学习中文多久了？你平时用中文做什么？
        第二个问题：你觉得中文最难的部分是什么？
        第三个问题：你能简单介绍一下你自己吗？
        
        请用中文回答以上问题。如果你觉得某个问题太难，可以用简单的词汇来表达。
        """
        
        user_response = self.chatbot.respond(initial_prompt)
        
        # detailed assessment criteria
        assessment_prompt = f"""
        请仔细分析用户的回答："{user_response}"
        
        评估标准：
        1. 词汇量 (占比30%):
           - 1级: 只会基础问候语和数字
           - 2级: 能使用150-300个基础词汇
           - 3级: 能使用300-600个常用词汇
           - 4级: 能使用600-1000个词汇，包括一些抽象词汇
           - 5级: 能使用1000-2000个词汇，表达更复杂的概念
           - 6级: 能使用2000个以上词汇，接近母语者水平
        
        2. 语法准确性 (占比30%):
           - 1级: 只能说单字或简单词组
           - 2级: 能组成简单句子，有基本语序
           - 3级: 能使用基础语法结构，但有明显错误
           - 4级: 能正确使用常见语法结构，偶有错误
           - 5级: 能熟练运用复杂语法结构
           - 6级: 语法使用自然，几乎没有错误
        
        3. 表达流畅度 (占比20%):
           - 1级: 只能回答是/否
           - 2级: 能用简单句子回答
           - 3级: 能进行基本对话
           - 4级: 能流畅表达简单话题
           - 5级: 能自然讨论较复杂话题
           - 6级: 表达流畅自然，接近母语者
        
        4. 理解能力 (占比20%):
           - 1级: 只能理解单个词汇
           - 2级: 能理解简单指令
           - 3级: 能理解日常对话
           - 4级: 能理解较复杂的表达
           - 5级: 能理解抽象概念
           - 6级: 理解能力接近母语者
        
        请根据以上标准分析用户回答，并给出以下格式的评估结果：
        级别: [1-6]
        置信度: [0-1]
        理由: [详细分析每个评估维度的表现，并说明最终评级的原因]
        """
        
        assessment_result = self.chatbot.respond(assessment_prompt)
        
        # parse the assessment result
        try:
            # extract the level and confidence from the AI response
            lines = assessment_result.split('\n')
            level = "1"
            confidence = 0.8
            
            for line in lines:
                line = line.strip()
                if line.startswith("级别:"):
                    level = line.split(":")[1].strip()
                elif line.startswith("置信度:"):
                    confidence = float(line.split(":")[1].strip())
            
            # ensure the level is in the valid range
            level = str(max(1, min(6, int(level))))
            confidence = max(0.0, min(1.0, confidence))
            
            return level, confidence
            
        except Exception as e:
            print(f"解析评估结果时出错: {e}")
            # if the parsing fails, return the current level and low confidence
            return current_level, 0.5
    
    def update_user_level(self, user_id: int, new_level: str) -> None:
        # ensure the new level is a number
        number_level = self._convert_hsk_to_number(new_level)
        self.store.update_language_level(user_id, number_level)
    
    def get_vocabulary_for_conversation(self, user_id: int, num_words: int = 5) -> List[str]:
        level = self.get_user_level(user_id)
        available_words = self.get_words_by_level(level)
        
        # if the number of words is less than num_words, and the level is not 1, then add the words of the previous level
        if len(available_words) < num_words and level != "1":
            previous_level = str(int(level) - 1)
            available_words.extend(self.get_words_by_level(previous_level))
        
        # random select num_words words
        import random
        selected_words = random.sample(available_words, min(num_words, len(available_words)))
        return selected_words
    
    def start_conversation_with_level_check(self, user_id: int) -> Tuple[List[str], str]:
        # assess the user level
        suggested_level, confidence = self.assess_user_level(user_id)
        current_level = self.get_user_level(user_id)
        
        # if the suggested level is different from the current level and the confidence is higher than the threshold
        if suggested_level != current_level and confidence > 0.8:
            self.update_user_level(user_id, suggested_level)
        
        # get the vocabulary for the conversation
        vocabulary = self.get_vocabulary_for_conversation(user_id)
        
        return vocabulary, suggested_level 