import pandas as pd

from src.reports import spending_by_category


# Тест 1: Базовый случай с категорией "Супермаркет"
def test_spending_by_category_basic(df_transactions: pd.DataFrame) -> None:
    df = pd.DataFrame(df_transactions)
    result = spending_by_category(df, "Супермаркет")
    assert not result.empty
    assert result["Категория"].unique()[0] == "Супермаркет"
    assert result["ИТОГО"].sum() == 7200.00


# Тест 2: Частичное совпадение категории
def test_spending_by_category_(df_transactions: pd.DataFrame) -> None:
    df = pd.DataFrame(df_transactions)
    result = spending_by_category(df, "развл")
    assert not result.empty
    assert result["Категория"].unique()[0] == "Развлечения"
    assert result["ИТОГО"].sum() == 13000.00
    assert result["ВСЕГО"].sum() == 6


# Тест 3: Не существующая категория
def test_spending_by_category_empty(df_transactions: pd.DataFrame) -> None:
    df = pd.DataFrame(df_transactions)
    result = spending_by_category(df, "Транспорт")
    assert result.empty
