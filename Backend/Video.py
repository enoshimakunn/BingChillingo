import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Backend.Speech import ASR
from Backend.Chatbot import Chat

class Video:
    def __init__(self):
        return NotImplementedError
    
    def run(self):
        return NotImplementedError