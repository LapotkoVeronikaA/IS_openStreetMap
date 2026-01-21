import requests
from flask import Flask
from app.utils import geocode_location
from app.config import Config

app = Flask(__name__)
app.config.from_object(Config)

def run_integration_test():
    test_address = "115432, г.Москва, 2-ой Кожуховский пр., д.12, стр.1"
    print(f"--- ЗАПУСК ТЕСТА ГЕОКОДИРОВАНИЯ ---")
    print(f"Входной адрес: {test_address}")

    with app.app_context():
        lat, lon = geocode_location(test_address)

        if lat and lon:
            print(f"УСПЕХ: Ответ от геокодера получен.")
            print(f"Результат парсинга featureMember:")
            print(f"  > Широта (Latitude): {lat} (Тип: {type(lat)})")
            print(f"  > Долгота (Longitude): {lon} (Тип: {type(lon)})")
        else:
            print("ОШИБКА: Не удалось получить данные от API.")

if __name__ == "__main__":
    run_integration_test()