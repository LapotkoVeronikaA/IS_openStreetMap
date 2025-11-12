# config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-very-secret-key-CHANGE-THIS'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///directory_database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False