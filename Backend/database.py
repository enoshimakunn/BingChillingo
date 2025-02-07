from datetime import datetime
import os
import sys
from typing import List, Optional

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Float, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Env import DATABASE_URL

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    speech_records = relationship("SpeechRecord", back_populates="user")
    learning_stats = relationship("LearningStats", back_populates="user")

class Conversation(Base):
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    vocabulary_used = Column(String(500))  # Store as comma-separated string
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'))
    content = Column(Text, nullable=False)
    is_user = Column(Boolean, default=True)  # True if message is from user, False if from AI
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

class SpeechRecord(Base):
    __tablename__ = 'speech_records'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    text = Column(Text, nullable=False)
    confidence_score = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="speech_records")

class LearningStats(Base):
    __tablename__ = 'learning_stats'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    vocabulary_mastered = Column(Integer, default=0)
    total_conversation_time = Column(Integer, default=0)  # in minutes
    last_practice = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="learning_stats")

class DatabaseManager:
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def create_user(self, username: str, email: str) -> User:
        user = User(username=username, email=email)
        self.session.add(user)
        self.session.commit()
        return user
    
    def get_user(self, user_id: int) -> Optional[User]:
        return self.session.query(User).filter(User.id == user_id).first()
    
    def create_conversation(self, user_id: int, vocabulary: List[str]) -> Conversation:
        conversation = Conversation(
            user_id=user_id,
            vocabulary_used=','.join(vocabulary)
        )
        self.session.add(conversation)
        self.session.commit()
        return conversation
    
    def add_message(self, conversation_id: int, content: str, is_user: bool) -> Message:
        message = Message(
            conversation_id=conversation_id,
            content=content,
            is_user=is_user
        )
        self.session.add(message)
        self.session.commit()
        return message
    
    def add_speech_record(self, user_id: int, text: str, confidence_score: float) -> SpeechRecord:
        record = SpeechRecord(
            user_id=user_id,
            text=text,
            confidence_score=confidence_score
        )
        self.session.add(record)
        self.session.commit()
        return record
    
    def update_learning_stats(self, user_id: int, vocab_mastered: int = None, 
                            conversation_time: int = None) -> LearningStats:
        stats = self.session.query(LearningStats).filter(
            LearningStats.user_id == user_id
        ).first()
        
        if not stats:
            stats = LearningStats(user_id=user_id)
            self.session.add(stats)
        
        if vocab_mastered is not None:
            stats.vocabulary_mastered = vocab_mastered
        if conversation_time is not None:
            stats.total_conversation_time += conversation_time
        
        stats.last_practice = datetime.utcnow()
        self.session.commit()
        return stats
    
    def close(self):
        self.session.close() 