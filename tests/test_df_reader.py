from unittest.mock import patch

import pandas as pd
from src.df_reader import load_and_convert_excel_to_dict


# Тест успешной загрузки и конвертации
def test_success_conversion(test_data: pd.DataFrame) -> None:
    # Создаем DataFrame для имитации чтения Excel
    df = pd.DataFrame(test_data)

    with patch("pandas.read_excel") as mock_read_excel:
        mock_read_excel.return_value = df
        result = load_and_convert_excel_to_dict("test.xlsx")

        expected_result = [
            {"Номер карты": "1234567890", "Кэшбэк": 100, "MCC": 5311, "Название": "Карта 1"},
            {"Номер карты": "2345678901", "Кэшбэк": 200, "MCC": 5411, "Название": "Карта 2"},
            {"Номер карты": "3456789012", "Кэшбэк": 300, "MCC": 5511, "Название": "Карта 3"},
        ]

        assert result == expected_result


# Тест с ошибкой файл не найден
def test_load_data_from_excel_missing_file() -> None:
    with patch("pandas.read_excel") as mock_read:
        mock_read.side_effect = FileNotFoundError
        result = load_and_convert_excel_to_dict("non_existent_file.xlsx")
        assert result == []


# Тест обработки общей ошибки
def test_general_error() -> None:
    with patch("pandas.read_excel") as mock_read_excel:
        mock_read_excel.side_effect = Exception("Test exception")
        result = load_and_convert_excel_to_dict("test.xlsx")
        assert result == []
