import os

import pandas as pd

file_path = os.path.join("..", "data", "operations.xlsx")


def load_data_from_excel(file_path: str) -> pd.DataFrame:
    """Загружает данные из Excel-файла в DataFrame"""
    # Читаем Exel файл
    try:
        # Читаем Exel файл
        df = pd.read_excel(file_path)
        # Заменяем пустые строки на NaN

        return df
    except FileNotFoundError:
        print(f"Файл {file_path} не найден")
        return []  # type: ignore
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        return []  # type: ignore


# df = load_data_from_excel(file_path)
def get_dict_from_df(data: pd.DataFrame) -> list[dict]:
    """Преобразует DataFrame в список словарей с обработкой пропущенных значений"""
    df = data.fillna({"Номер карты": "Нет данных", "Кэшбэк": 0, "MCC": 0})
    result = df.to_dict("records")
    return result


#
# # Пример использования
# if __name__ == "__main__":
#     # Указываем путь к файлу
#     file_path = os.path.join("..", "data", "operations.xlsx")
#
#     # Загружаем данные
#     df = load_data_from_excel(file_path)
#
#     if not df.empty:
#         # Преобразуем в список словарей
#         data_dict = get_dict_from_df(df)
#
#         # Выводим результат
#         print(data_dict)
#     else:
#         print("Данные не были загружены")
