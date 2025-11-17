# app/config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-very-secret-key-CHANGE-THIS'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///directory_database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    YANDEX_GEOCODER_API_KEY = "bf6a5825-d12d-4d1d-8800-066f5f2f3003"
    
    API_SECRET_KEY = os.environ.get('API_SECRET_KEY') or 'super-secret-api-key'