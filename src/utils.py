import json
import logging
import os
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import requests
from dotenv import load_dotenv

# Загрузка переменных из .env-файла
load_dotenv()

API_KEY = os.getenv("APILAYER_KEY")
API_NINJAS_KEY = os.getenv("API_NINJAS_KEY")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def parse_date(date_str: str) -> pd.Timestamp:
    """
    Универсальный парсер для дат: автоматически определяет dayfirst.
    """
    # YYYY-MM-DD или YYYY/MM/DD (дефис или слэш на позиции 4)
    if ("-" in date_str and date_str.index("-") == 4) or ("/" in date_str and date_str.index("/") == 4):
        return pd.to_datetime(date_str, dayfirst=False)
    # Всё остальное — dayfirst: ДД.ММ.ГГГГ, ДД-ММ-ГГГГ, ДД/ММ/ГГГГ и т.п.
    return pd.to_datetime(date_str, dayfirst=True)


def filter_by_range(df: pd.DataFrame, date_str: str, range_type: str = "M") -> pd.DataFrame:
    """
    Фильтрует DataFrame по диапазону дат.
    """
    logger.info(f"Фильтрация данных: date={date_str}, range_type={range_type}")
    try:
        date = parse_date(date_str)
        df["Дата операции"] = pd.to_datetime(
            df["Дата операции"], dayfirst=True
        )  # Можно вынести в parse_date, если надо
        if range_type == "W":
            start = date - timedelta(days=date.weekday())  # Понедельник текущей недели
        elif range_type == "M":
            start = date.replace(day=1)  # Первый день месяца
        elif range_type == "Y":
            start = date.replace(month=1, day=1)  # Первый день года
        elif range_type == "ALL":
            start = df["Дата операции"].min()  # Минимальная дата
        else:
            start = date  # Просто сам день (fallback)
        end = date
        logger.info(f"Диапазон дат: {start} - {end}")
        return df.loc[(df["Дата операции"] >= start) & (df["Дата операции"] <= end)]
    except Exception as e:
        logger.error(f"Ошибка фильтрации по дате: {e}")
        return df.iloc[0:0]  # Возвращаем пустой DataFrame, если ошибка


def get_expenses_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Собирает данные о расходах согласно ТЗ и возвращает результат с ключом 'expenses'.
    """
    logger.info("Агрегация расходов...")
    try:
        exp = df[(df["Сумма операции"] < 0) & (df["Статус"] == "OK")]
        total = round(abs(exp["Сумма операции"].sum()), 2)  # округление здесь

        cat_exp = exp.groupby("Категория")["Сумма операции"].sum().abs().sort_values(ascending=False)

        # округляем значения прямо в comprehension
        cats = {k: round(v, 2) for k, v in cat_exp.head(7).items()}
        other = round(cat_exp.iloc[7:].sum(), 2)
        if other > 0:
            cats["Остальное"] = other

        # округляем переводы и наличные также inline
        cash_trans = exp[exp["Категория"].isin(["Переводы", "Наличные"])]
        trans_sum = {
            k: round(v, 2)
            for k, v in cash_trans.groupby("Категория")["Сумма операции"]
            .sum()
            .abs()
            .sort_values(ascending=False)
            .items()
        }

        return {
            "expenses": {
                "Общая сумма": total,
                "Основные": cats,
                "Переводы и наличные": trans_sum,
            }
        }
    except Exception as e:
        logger.error("Ошибка агрегации расходов: %s", e)
        return {"expenses": {"Общая сумма": 0.0, "Основные": {}, "Переводы и наличные": {}}}


def get_incomes_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Собирает данные о поступлениях согласно ТЗ и возвращает
    структурированный JSON‑словарь в едином формате.
    """
    logger.info("Агрегация поступлений...")
    try:
        inc = df[(df["Сумма операции"] > 0) & (df["Статус"] == "OK")]
        total = round(inc["Сумма операции"].sum(), 2)  # округление общей суммы

        # все значения категорий округляются в comprehension
        cats = {
            k: round(v, 2)
            for k, v in inc.groupby("Категория")["Сумма операции"].sum().sort_values(ascending=False).items()
        }

        return {"incomes": {"Общая сумма": total, "Основные": cats}}
    except Exception as e:
        logger.error("Ошибка агрегации поступлений: %s", e)
        return {"incomes": {"Общая сумма": 0.0, "Основные": {}}}


def get_exchange_rates(date_str: str) -> Dict[str, Any]:
    """
    Получает курсы валют USD и EUR относительно RUB на дату date_str.
    """
    settings_path = Path(__file__).parent.parent / "data" / "user_settings.json"
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
        currencies = settings.get("user_currencies", [])
        if not currencies:
            raise ValueError("Нет валют в настройках")
        symbols = ",".join(currencies)
        date_iso = parse_date(date_str).strftime("%Y-%m-%d")
        url = f"https://api.apilayer.com/exchangerates_data/{date_iso}"
        params = {"base": "RUB", "symbols": symbols}
        headers = {"apikey": API_KEY}
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        rates = data.get("rates", {})
        result = [{"currency": c, "rate": round(1 / rates[c], 2)} for c in currencies if c in rates and rates[c]]
        logger.info(f"Курсы валют: {result}")
        return {"currency_rates": result}
    except Exception as e:
        logger.error("Ошибка получения курсов валют: %s", e)
        return {"currency_rates": []}


def get_sp500_quotes(date_str: str) -> Dict[str, Any]:
    """Получает исторические котировки акций S&P500 (если доступно через API Ninjas)"""
    settings_path = Path(__file__).parent.parent / "data" / "user_settings.json"
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
        tickers = settings.get("user_stocks", [])
    except Exception as e:
        logger.error("Ошибка чтения user_settings.json: %s", e)
        return {"stock_prices": []}

    # Форматируем дату и диапазон времени в часах (на всякий случай 6 часов)
    start = int(parse_date(date_str).timestamp())
    end = int((parse_date(date_str) + timedelta(hours=6)).timestamp())

    url_hist = "https://api.api-ninjas.com/v1/stockpricehistorical"
    url_now = "https://api.api-ninjas.com/v1/stockprice"
    headers = {"X-Api-Key": API_NINJAS_KEY}
    results = []

    for ticker in tickers:
        try:
            # Сначала пытаемся получить исторические данные
            params = {"ticker": ticker, "period": "1h", "start": start, "end": end}
            response = requests.get(url_hist, headers=headers, params=params)

            if response.status_code == 400:
                # Если исторические данные недоступны, берём текущую цену
                response = requests.get(url_now, headers=headers, params={"ticker": ticker})

            response.raise_for_status()
            data = response.json()

            # Если это исторические данные — берём 'close' последней записи
            if isinstance(data, list) and len(data) > 0:
                close = data[-1].get("close")
                price = round(close, 2) if isinstance(close, (int, float)) else None
            elif isinstance(data, dict) and "price" in data:
                price = round(data["price"], 2)
            else:
                price = None

            results.append({"stock": ticker, "price": price})
        except Exception as e:
            logger.error("Ошибка при получении котировок %s: %s", ticker, e)
            results.append({"stock": ticker, "price": None})

    logger.info(f"Котировки на {date_str} получены.")
    return {"stock_prices": results}
