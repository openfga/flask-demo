# config.py

import os
from dotenv import load_dotenv

class Config:
    load_dotenv()
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///db.sqlite3')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FGA_API_URL = os.getenv('FGA_API_URL', 'http://localhost:8080')
    FGA_STORE_ID = os.getenv('FGA_STORE_ID')
    FGA_MODEL_ID = os.getenv('FGA_MODEL_ID')
