import os
import sys

from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Backend.database import Base
from Env import DATABASE_URL

def init_database():
    # Create engine
    engine = create_engine(DATABASE_URL)
    
    # Create database if it doesn't exist
    if not database_exists(engine.url):
        create_database(engine.url)
        print(f"Created database")
    
    # Create all tables
    Base.metadata.create_all(engine)
    print(f"Created all tables")

if __name__ == "__main__":
    init_database() 