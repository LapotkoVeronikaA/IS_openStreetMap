# app/config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or '70192100_api_key'
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, '..', 'app.db')

    # Отключаем отслеживание изменений для экономии памяти
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # API ключ Яндекс.Геокодера
    YANDEX_GEOCODER_API_KEY = "yandex-geocoder-api-key"
    
    # Ключ для доступа к API
    API_SECRET_KEY = os.environ.get('API_SECRET_KEY') or '70192100_api_secret_key'
    
    # Лимит на размер загружаемых файлов (100МБ)
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024