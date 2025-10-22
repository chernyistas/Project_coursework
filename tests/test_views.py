from unittest.mock import patch
import pandas as pd
from src.views import get_events

def test_get_events(tmp_path):
    df = pd.DataFrame({
        'Дата операции': ['01.10.2025 12:12:10'],
        'Сумма операции': [-1200],
        'Категория': ['Супермаркеты'],
        'Статус': ['OK']
    })

    with patch('src.views.pd.read_excel', return_value=df), \
         patch('src.views.get_exchange_rates', return_value=[{"currency": "USD", "rate": 73.0}]), \
         patch('src.views.get_sp500_quotes', return_value=[{"stock": "AAPL", "price": 150.0}]):
        result = get_events("01.10.2025")
        assert "Расходы" in result or "expenses" in result
        assert "Поступления" in result or "income" in result