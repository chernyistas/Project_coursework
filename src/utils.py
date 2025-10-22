import logging
import pandas as pd
from datetime import datetime, timedelta
import requests
import json
import requests
import os
from dotenv import load_dotenv
from pathlib import Path

# Загрузка переменных из .env-файла
load_dotenv()

API_KEY = os.getenv("APILAYER_KEY")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def filter_by_range(df, date_str, range_type):

    """
    Фильтрует DataFrame по диапазону дат.
    """
    logger.info(f"Фильтрация данных: date={date_str}, range_type={range_type}")
    try:
        date = pd.to_datetime(date_str)
        logger.debug(f"Дата преобразована: {date}")
        if range_type == 'W':
            start = date - timedelta(days=date.weekday())  # начало недели
        elif range_type == 'M':
            start = date.replace(day=1)
        elif range_type == 'Y':
            start = date.replace(month=1, day=1)
        elif range_type == 'ALL':
            start = df['Дата операции'].min()
        else:
            start = date.replace(day=1)
        end = date
        df['Дата операции'] = pd.to_datetime(df['Дата операции'], dayfirst=True)
        logger.info(f"Диапазон дат: {start} - {end}")
        return df[(df['Дата операции'] >= start) & (df['Дата операции'] <= end)]
    except Exception as e:
        logger.error(f"Ошибка фильтрации по дате: {e}")
        raise

def get_expenses_summary(df):
    """
    Собирает данные о расходах согласно ТЗ.
    """
    logger.info("Агрегация расходов...")
    # Считаем сумму расходов (отрицательные суммы, статусы ОК)
    try:
        exp = df[(df['Сумма операции'] < 0) & (df['Статус'] == 'OK')]
        total_exp = exp['Сумма операции'].sum()
        # Категории
        cat_exp = exp.groupby('Категория')['Сумма операции'].sum().abs().sort_values(ascending=False)
        major_cats = cat_exp[:7]
        other_cats = cat_exp[7:].sum()
        cats_dict = major_cats.to_dict()
        if other_cats > 0:
            cats_dict['Остальное'] = other_cats
        # Переводы и наличные
        trans = exp[exp['Категория'].isin(['Переводы', 'Наличные'])]
        trans_sum = trans.groupby('Категория')['Сумма операции'].sum().abs().sort_values(ascending=False).to_dict()
        logger.info(f"Расходы собраны: {cats_dict}")
        return {
            "Общая сумма": float(abs(total_exp)),
            "Основные": cats_dict,
            "Переводы и наличные": trans_sum
        }
    except Exception as e:
        logger.error(f"Ошибка агрегации расходов: {e}")
        raise


def get_incomes_summary(df):
    """
    Собирает данные о поступлениях согласно ТЗ.
    """
    inc = df[(df['Сумма операции'] > 0) & (df['Статус'] == 'OK')]
    total_inc = inc['Сумма операции'].sum()
    cat_inc = inc.groupby('Категория')['Сумма операции'].sum().sort_values(ascending=False).to_dict()
    return {
        "Общая сумма": float(total_inc),
        "Основные": cat_inc
    }


def get_exchange_rates(date_str):
    """
    Получить курсы валют USD и EUR относительно RUB на дату date_str.
    """
    settings_path = Path(__file__).parent / "data" / "user_settings.json"
    with open(settings_path, "r", encoding="utf-8") as f:
        settings = json.load(f)
    user_currencies = settings.get("user_currencies", [])
    symbols_str = ",".join(user_currencies)

    # endpoint для исторических курсов
    url = f"https://api.apilayer.com/exchangerates_data/{date_str}"
    params = {
        "base": "USD",
        "symbols": symbols_str
    }
    headers = {"apikey": API_KEY}
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        rates = data.get("rates", {})
        # USD/RUB — сколько рублей за доллар (будет всегда 1 RUB, если base='RUB')
        usd_rub = rates.get("RUB")
        eur_rub = None
        # Если base=USD, EUR это сколько евро за доллар, RUB — сколько рублей за доллар
        if "EUR" in rates:
            eur_rub = rates["EUR"]  # это курс EUR/USD, можно получить RUB/EUR через обратную операцию
        result = []
        if usd_rub is not None:
            result.append({"currency": "USD", "rate": usd_rub})
        if eur_rub is not None:
            # Если хотим RUB/EUR — сделайте RUB/USD / EUR/USD
            # А если просто EUR/USD, оставьте так:
            result.append({"currency": "EUR", "rate": eur_rub})
        return {"currency_rates": result}
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        return {"currency_rates": []}

# def get_sp500_quotes(date_str):
#     logger.info(f"Запрос стоимости S&P 500 на дату {date_str}")
#     try:
#         response = requests.get(f'https://example.com/sp500?date={date_str}')
#         response.raise_for_status()
#         logger.info(f"Котировки акций получены")
#         return response.json()
#     except Exception as e:
#         logger.error(f"Ошибка запроса котировок S&P 500: {e}")
#         return {}
