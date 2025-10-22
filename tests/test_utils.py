import json
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.utils import filter_by_range, get_exchange_rates, get_expenses_summary, get_incomes_summary, get_sp500_quotes


@pytest.mark.parametrize("range_type", ["W", "M", "Y", "ALL", "UNKNOWN"])
def test_filter_by_range_variants(sample_df, range_type):
    filtered = filter_by_range(sample_df.copy(), "2025-10-01", range_type)
    assert isinstance(filtered, pd.DataFrame)
    assert "Дата операции" in filtered.columns


def test_filter_by_range_invalid_date(sample_df):
    with pytest.raises(Exception):
        filter_by_range(sample_df.copy(), "invalid-date", "M")


def test_filter_by_range_week(sample_df):
    from datetime import datetime

    df_filtered = filter_by_range(sample_df, "2025-10-02", "W")
    assert not df_filtered.empty
    assert all(isinstance(x, datetime) for x in df_filtered["Дата операции"])


def test_get_incomes_summary(sample_df):
    result = get_incomes_summary(sample_df)
    assert "incomes" in result
    assert "Общая сумма" in result["incomes"]
    assert result["incomes"]["Общая сумма"] == 1000.0
    assert "Основные" in result["incomes"]
    assert "Зарплата" in result["incomes"]["Основные"]


def test_get_incomes_summary_with_error(monkeypatch):
    def bad_groupby(*args, **kwargs):
        raise Exception("Ошибка groupby")

    monkeypatch.setattr(pd.DataFrame, "groupby", bad_groupby)
    result = get_incomes_summary(pd.DataFrame())
    assert result["incomes"]["Общая сумма"] == 0.0


def test_get_expenses_summary(sample_df):
    result = get_expenses_summary(sample_df)
    assert "expenses" in result
    assert round(result["expenses"]["Общая сумма"], 2) == 700.0
    assert "Еда" in result["expenses"]["Основные"]
    assert "Переводы и наличные" in result["expenses"]


def test_get_expenses_summary_with_error(monkeypatch):
    def bad_filter(*args, **kwargs):
        raise Exception("ошибка фильтрации")

    monkeypatch.setattr(pd.DataFrame, "__getitem__", bad_filter)
    result = get_expenses_summary(pd.DataFrame())
    assert result["expenses"]["Общая сумма"] == 0.0


@patch("requests.get")
def test_get_exchange_rates(mock_get, tmp_path):

    # Создаём временную структуру каталогов: src/ и data/
    src_dir = tmp_path / "src"
    data_dir = tmp_path / "data"
    src_dir.mkdir()
    data_dir.mkdir()

    # Создаём фиктивный utils.py, чтобы функция думала, что находится в src/
    dummy_file = src_dir / "utils.py"
    dummy_file.write_text("")

    # Создаём user_settings.json в data/
    settings_path = data_dir / "user_settings.json"
    settings_path.write_text(json.dumps({"user_currencies": ["USD", "EUR"]}), encoding="utf-8")

    # Поддельный ответ API от apilayer
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"rates": {"USD": 0.0137, "EUR": 0.0115}}
    mock_get.return_value = mock_response

    # Импортируем модуль utils и подменяем __file__, чтобы src/ была в tmp_path/src
    import src.utils as utils

    utils.__file__ = str(dummy_file)

    # Вызываем функцию
    result = get_exchange_rates("latest")

    # Если результат возвращён как строка — преобразуем в словарь
    if isinstance(result, str):
        result = json.loads(result)

    # Проверяем корректность структуры и данных
    assert "currency_rates" in result
    assert any(c["currency"] == "USD" for c in result["currency_rates"])
    assert all("currency" in c and "rate" in c for c in result["currency_rates"])


@patch("requests.get")
def test_get_sp500_quotes(mock_get, tmp_path):

    # Создаём временную структуру каталогов: src/ и data/
    src_dir = tmp_path / "src"
    data_dir = tmp_path / "data"
    src_dir.mkdir()
    data_dir.mkdir()

    # Создаём фиктивный utils.py внутри src — чтобы __file__ указывал в src/
    dummy_file = src_dir / "utils.py"
    dummy_file.write_text("")

    # Создаём user_settings.json в папке data/
    settings_path = data_dir / "user_settings.json"
    settings_path.write_text(json.dumps({"user_stocks": ["AAPL", "AMZN"]}), encoding="utf-8")

    # Поддельный ответ API Ninjas
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"ticker": "AAPL", "price": 150.25}
    mock_get.return_value = mock_response

    # Импортируем src.utils и подменяем __file__, чтобы относительный путь вел к tmp_path/src/
    import src.utils as utils

    utils.__file__ = str(dummy_file)

    # Вызываем тестируемую функцию
    result = get_sp500_quotes("2025-10-22")

    # Если результат возвращён как строка — декодируем в dict
    if isinstance(result, str):
        result = json.loads(result)

    # Проверяем корректность структуры и данных
    assert "stock_prices" in result
    assert any(s["stock"] == "AAPL" for s in result["stock_prices"])
    assert all("stock" in s and "price" in s for s in result["stock_prices"])
