import json
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest

import src.utils as utils
from src.utils import filter_by_range, get_expenses_summary, get_incomes_summary, get_sp500_quotes


@pytest.mark.parametrize("range_type", ["W", "M", "Y", "ALL", "UNKNOWN"])
def test_filter_by_range_variants(sample_df: pd.DataFrame, range_type: str) -> None:
    # Проверяет работу диапазонов фильтрации.

    filtered = filter_by_range(sample_df.copy(), "2025-10-01", range_type)
    assert isinstance(filtered, pd.DataFrame)
    assert "Дата операции" in filtered.columns


def test_filter_by_range_week(sample_df: pd.DataFrame) -> None:
    # Проверка фильтрации по неделе.

    from datetime import datetime

    df_filtered = filter_by_range(sample_df, "2025-10-02", "W")
    assert not df_filtered.empty
    assert all(isinstance(x, datetime) for x in df_filtered["Дата операции"])


def test_get_incomes_summary(sample_df: pd.DataFrame) -> None:
    # Проверка корректной агрегации поступлений.

    result = get_incomes_summary(sample_df)
    assert "incomes" in result
    assert "Общая сумма" in result["incomes"]
    assert result["incomes"]["Общая сумма"] == 1000.0
    assert "Основные" in result["incomes"]
    assert "Зарплата" in result["incomes"]["Основные"]


def test_get_incomes_summary_with_error(monkeypatch: Any) -> None:
    # Проверка реакции на ошибку фильтрации.

    def bad_groupby(*args: Any, **kwargs: Any) -> Any:
        raise Exception("Ошибка groupby")

    monkeypatch.setattr(pd.DataFrame, "groupby", bad_groupby)
    result = get_incomes_summary(pd.DataFrame())
    assert result["incomes"]["Общая сумма"] == 0.0


def test_get_expenses_summary(sample_df):  # type: ignore
    # Проверка реакции на ошибку фильтрации.

    result = get_expenses_summary(sample_df)
    assert "expenses" in result
    assert round(result["expenses"]["Общая сумма"], 2) == 700.0
    assert "Еда" in result["expenses"]["Основные"]
    assert "Переводы и наличные" in result["expenses"]


def test_get_expenses_summary_with_error(monkeypatch: Any) -> None:
    # Проверка реакции на ошибку фильтрации.

    def bad_filter(*args: Any, **kwargs: Any) -> Any:
        raise Exception("ошибка фильтрации")

    monkeypatch.setattr(pd.DataFrame, "__getitem__", bad_filter)
    result = get_expenses_summary(pd.DataFrame())
    assert result["expenses"]["Общая сумма"] == 0.0


@patch("src.utils.requests.get")
def test_get_exchange_rates(mock_get: Mock, tmp_path: Any) -> None:
    # Тест получения курсов валют с мокированным requests.get.

    # === 1. Создание временной структуры ===
    src_dir = tmp_path / "src"
    data_dir = tmp_path / "data"
    src_dir.mkdir()
    data_dir.mkdir()

    dummy_file = src_dir / "utils.py"
    dummy_file.write_text("")  # фиктивный utils.py, чтобы работал parent.parent

    # === 2. Конфигурация user_settings.json ===
    settings = {"user_currencies": ["USD", "EUR"]}
    settings_path = data_dir / "user_settings.json"
    settings_path.write_text(json.dumps(settings), encoding="utf-8")

    # === 3. Настройка mock-ответа API apilayer ===
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"rates": {"USD": 0.0137, "EUR": 0.0115}}
    mock_get.return_value = mock_response

    # Функция использует Path(__file__) → подменим путь
    utils.__file__ = str(dummy_file)

    # === 4. Вызов тестируемой функции ===
    result = utils.get_exchange_rates("20-05-2019")

    # === 5. Проверки результата ===
    assert isinstance(result, dict)
    assert "currency_rates" in result
    assert isinstance(result["currency_rates"], list)

    # Проверяем, что обе валюты присутствуют
    currencies = [c["currency"] for c in result["currency_rates"]]
    assert "USD" in currencies
    assert "EUR" in currencies

    # Проверяем корректность округления и структуры
    for rate_info in result["currency_rates"]:
        assert isinstance(rate_info["rate"], float)
        frac = str(rate_info["rate"]).split(".")[-1]
        assert len(frac) <= 2  # не более двух знаков после запятой

    # Убеждаемся, что запрос был выполнен один раз
    mock_get.assert_called_once()

    # Проверяем, что запрос был отправлен на правильный URL
    called_url = mock_get.call_args[0][0]
    assert "https://api.apilayer.com/exchangerates_data/" in called_url


@patch("requests.get")
def test_get_sp500_quotes(mock_get: Mock, tmp_path: Any) -> None:
    # Тест получения котировок S&P 500.

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
