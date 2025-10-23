import json
from unittest.mock import Mock, patch

import pandas as pd

from src.views import get_events

# Успешный сценарий


@patch("src.views.pd.read_excel")
@patch("src.views.get_exchange_rates")
@patch("src.views.get_sp500_quotes")
@patch("src.views.get_expenses_summary")
@patch("src.views.get_incomes_summary")
@patch("src.views.filter_by_range")
def test_get_events_success(
    mock_filter_by_range: Mock,
    mock_get_incomes_summary: Mock,
    mock_get_expenses_summary: Mock,
    mock_get_sp500_quotes: Mock,
    mock_get_exchange_rates: Mock,
    mock_read_excel: Mock,
) -> None:
    # Тест успешного сценария выполнения get_events.

    # Поддельный DataFrame для excel
    df = pd.DataFrame(
        {
            "Дата операции": ["2025-10-01", "2025-10-10"],
            "Сумма операции": [100, -50],
            "Категория": ["Зарплата", "Еда"],
            "Статус": ["OK", "OK"],
        }
    )
    mock_read_excel.return_value = df
    mock_filter_by_range.return_value = df

    # Возвращаем предопределённые данные из зависимостей
    mock_get_incomes_summary.return_value = {"incomes": {"Общая сумма": 100, "Основные": {"Зарплата": 100}}}
    mock_get_expenses_summary.return_value = {"expenses": {"Общая сумма": 50, "Основные": {"Еда": 50}}}
    mock_get_exchange_rates.return_value = {"currency_rates": [{"currency": "USD", "rate": 74.2}]}
    mock_get_sp500_quotes.return_value = {"stock_prices": [{"stock": "AAPL", "price": 150.0}]}

    # Вызов функции
    result_str = get_events("2025-10-20", "M")
    result = json.loads(result_str)

    # Проверка структуры
    assert "Расходы" in result
    assert "Поступления" in result
    assert "Курс валют" in result
    assert "Стоимость акций S&P 500" in result

    # Проверяем, что суммы и курсы корректны
    assert result["Поступления"]["incomes"]["Общая сумма"] == 100
    assert any(c["currency"] == "USD" for c in result["Курс валют"]["currency_rates"])


# НЕ УДАЛОСЬ ПРОЧИТАТЬ EXCEL


@patch("src.views.pd.read_excel", side_effect=FileNotFoundError("Нет файла"))
def test_get_events_excel_not_found(mock_read_excel: Mock) -> None:
    # Тест — Excel не найден.

    result_str = get_events("2025-10-22")
    result = json.loads(result_str)
    assert "error" in result
    assert "Нет файла" in result["error"]


# ОШИБКА ВО ВРЕМЯ ПОЛУЧЕНИЯ ЗНАЧЕНИЙ ИЗ API


@patch("src.views.pd.read_excel")
@patch("src.views.filter_by_range")
@patch("src.views.get_exchange_rates", side_effect=Exception("Ошибка API"))
def test_get_events_error_in_exchange_api(
    mock_get_ex: Mock,
    mock_filter_by_range: Mock,
    mock_read_excel: Mock,
) -> None:  # Тест — исключение при получении курсов валют.

    df = pd.DataFrame(
        {"Дата операции": ["2025-10-01"], "Сумма операции": [100], "Категория": ["Зарплата"], "Статус": ["OK"]}
    )
    mock_read_excel.return_value = df
    mock_filter_by_range.return_value = df

    result_str = get_events("2025-10-22")
    result = json.loads(result_str)
    assert "error" in result
    assert "Ошибка API" in result["error"]
