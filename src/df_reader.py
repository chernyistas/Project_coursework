import pandas as pd


def load_and_convert_excel_to_dict(file_path: str) -> list[dict]:
    """
    Загружает данные из Excel-файла и преобразует их в список словарей
    с обработкой пропущенных значений

    """
    try:
        # Читаем Excel файл
        df = pd.read_excel(file_path)

        # Обрабатываем пропущенные значения
        df = df.fillna({"Номер карты": "Нет данных", "Кэшбэк": 0, "MCC": 0})

        # Преобразуем в список словарей
        result = df.to_dict("records")
        return result

    except FileNotFoundError:
        print(f"Файл {file_path} не найден")
        return []

    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        return []
