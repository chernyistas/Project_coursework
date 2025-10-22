import pandas as pd
import pytest
from src.utils import (
    filter_by_range,
    get_expenses_summary,
    get_incomes_summary,
    # get_exchange_rates,
    # get_sp500_quotes
)
from unittest.mock import patch, Mock

def sample_df():
    return pd.DataFrame({
        'Дата операции': [
            '01.10.2025 12:20:15',
            '05.10.2025 15:45:00',
            '10.10.2025 09:10:05',
            '12.10.2025 14:22:00',
            '18.10.2025 11:10:00'
        ],
        'Сумма операции': [-1000, 2000, -3500, 700, -500],
        'Категория': ['Супермаркеты', 'Пополнение_BANK007', 'Фастфуд', 'Кэшбэк', 'Переводы'],
        'Статус': ['OK', 'OK', 'OK', 'OK', 'OK']
    })

def test_filter_by_range_month():
    df = sample_df()
    df_filtered = filter_by_range(df, '18.10.2025', 'M')
    assert len(df_filtered) == 5

def test_filter_by_range_week():
    df = sample_df()
    df_filtered = filter_by_range(df, '10.10.2025', 'W')
    assert all(isinstance(date, pd.Timestamp) for date in df_filtered['Дата операции'])

def test_get_expenses_summary():
    df = sample_df()
    summary = get_expenses_summary(df)
    assert 'Общая сумма' in summary
    assert summary["Общая сумма"] == 5000

def test_get_incomes_summary():
    df = sample_df()
    summary = get_incomes_summary(df)
    assert 'Общая сумма' in summary
    assert summary['Общая сумма'] == 2700

def test_get_exchange_rates():
    with patch('utils.requests.get') as mock_get:
        mock_resp = Mock()
        mock_resp.json.return_value = {"USD": 73.21, "EUR": 87.08}
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp
        result = get_exchange_rates("18.10.2025")
        assert "USD" in result
        assert result["USD"] == 73.21

def test_get_sp500_quotes():
    with patch('utils.requests.get') as mock_get:
        mock_resp = Mock()
        mock_resp.json.return_value = {"AAPL": 150.1, "GOOGL": 2742.39}
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp
        result = get_sp500_quotes("18.10.2025")
        assert "AAPL" in result