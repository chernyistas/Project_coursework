import os

import pandas as pd

file_path = os.path.join("..", "data", "operations.xlsx")


def load_data_from_exel(file_path: str) -> list[dict]:
    """Функция, которая считывает данные из Exel файла и возвращает список словарей"""
    # Читаем Exel файл
    try:
        # Читаем Exel файл
        df = pd.read_excel(file_path)
        # Заменяем пустые строки на NaN
        df = df.fillna({"Номер карты": "Нет данных", "Кэшбэк": 0, "MCC": 0})

        result = df.to_dict("records")
        return result
    except FileNotFoundError:
        print(f"Файл {file_path} не найден")
        return []
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        return []


print(load_data_from_exel(file_path))
