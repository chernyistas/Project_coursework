import json
import logging
import os
from datetime import timedelta
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

# Загрузка переменных из .env-файла
load_dotenv()

API_KEY = os.getenv("APILAYER_KEY")
API_NINJAS_KEY = os.getenv("API_NINJAS_KEY")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def filter_by_range(df, date_str, range_type):
    """
    Фильтрует DataFrame по диапазону дат.
    """
    logger.info(f"Фильтрация данных: date={date_str}, range_type={range_type}")
    try:
        date = pd.to_datetime(date_str)
        logger.debug(f"Дата преобразована: {date}")
        if range_type == "W":
            start = date - timedelta(days=date.weekday())  # начало недели
        elif range_type == "M":
            start = date.replace(day=1)
        elif range_type == "Y":
            start = date.replace(month=1, day=1)
        elif range_type == "ALL":
            start = df["Дата операции"].min()
        else:
            start = date.replace(day=1)
        end = date
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
        logger.info(f"Диапазон дат: {start} - {end}")
        return df[(df["Дата операции"] >= start) & (df["Дата операции"] <= end)]
    except Exception as e:
        logger.error(f"Ошибка фильтрации по дате: {e}")
        raise


def get_expenses_summary(df):
    """
    Собирает данные о расходах согласно ТЗ и возвращает результат с ключом 'expenses'.
    """
    logger.info("Агрегация расходов...")
    try:
        exp = df[(df["Сумма операции"] < 0) & (df["Статус"] == "OK")]
        total_exp = exp["Сумма операции"].sum()
        cat_exp = exp.groupby("Категория")["Сумма операции"].sum().abs().sort_values(ascending=False)
        major_cats = cat_exp[:7]
        other_cats = cat_exp[7:].sum()
        cats_dict = major_cats.to_dict()
        if other_cats > 0:
            cats_dict["Остальное"] = other_cats
        trans = exp[exp["Категория"].isin(["Переводы", "Наличные"])]
        trans_sum = trans.groupby("Категория")["Сумма операции"].sum().abs().sort_values(ascending=False).to_dict()
        logger.info(f"Расходы собраны: {cats_dict}")
        result = {
            "expenses": {"Общая сумма": float(abs(total_exp)), "Основные": cats_dict, "Переводы и наличные": trans_sum}
        }
        return result
    except Exception as e:
        logger.error(f"Ошибка агрегации расходов: {e}")
        return {"expenses": {"Общая сумма": 0.0, "Основные": {}, "Переводы и наличные": {}}}


def get_incomes_summary(df):
    """
    Собирает данные о поступлениях согласно ТЗ и возвращает
    структурированный JSON‑словарь в едином формате.
    """
    logger.info("Агрегация поступлений...")
    try:
        inc = df[(df["Сумма операции"] > 0) & (df["Статус"] == "OK")]
        total_inc = inc["Сумма операции"].sum()
        cat_inc = inc.groupby("Категория")["Сумма операции"].sum().sort_values(ascending=False).to_dict()

        logger.info(f"Поступления собраны: {cat_inc}")
        result = {"incomes": {"Общая сумма": float(total_inc), "Основные": cat_inc}}
        return result
    except Exception as e:
        logger.error(f"Ошибка агрегации поступлений: {e}")
        return {"incomes": {"Общая сумма": 0.0, "Основные": {}}}


def get_exchange_rates(date_str):
    """
    Получить курсы валют USD и EUR относительно RUB на дату date_str.
    """
    settings_path = Path(__file__).parent.parent / "data" / "user_settings.json"
    with open(settings_path, "r", encoding="utf-8") as f:
        settings = json.load(f)
    user_currencies = settings.get("user_currencies", [])
    symbols_str = ",".join(user_currencies)

    url = f"https://api.apilayer.com/exchangerates_data/{date_str}"
    params = {"base": "RUB", "symbols": symbols_str}
    headers = {"apikey": API_KEY}

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        rates = data.get("rates", {})
        result = [
            {"currency": c, "rate": round(1 / rates[c], 2)}  # округляем до 2 знаков
            for c in user_currencies
            if c in rates
        ]
        formatted = {"currency_rates": result}
        logging.info(f"Форматированный результат: {formatted}")
        return formatted
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        return json.dumps({"currency_rates": []}, ensure_ascii=False, indent=2)


def get_sp500_quotes(date_str: str):
    """
    Получает котировки акций из user_settings.json
    """
    # Путь к файлу с пользовательскими настройками
    settings_path = Path(__file__).parent.parent / "data" / "user_settings.json"
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
        tickers = settings.get("user_stocks", [])
    except FileNotFoundError:
        logger.error(f"Файл user_settings.json не найден по пути {settings_path}")
        return json.dumps({"stock_prices": []}, ensure_ascii=False, indent=2)
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка чтения JSON из {settings_path}: {e}")
        return json.dumps({"stock_prices": []}, ensure_ascii=False, indent=2)

    url = "https://api.api-ninjas.com/v1/stockprice"
    headers = {"X-Api-Key": API_NINJAS_KEY}
    result = {"stock_prices": []}

    logger.info(f"Запрос котировок акций из списка: {tickers} на дату {date_str}")

    for ticker in tickers:
        try:
            response = requests.get(url, headers=headers, params={"ticker": ticker})
            response.raise_for_status()
            data = response.json()

            if "price" in data and "ticker" in data:
                result["stock_prices"].append({"stock": data["ticker"], "price": round(data["price"], 2)})
            else:
                result["stock_prices"].append({"stock": ticker, "price": None})

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при получении котировок для {ticker}: {e}")
            result["stock_prices"].append({"stock": ticker, "price": None})

    logger.info("Котировки успешно собраны.")
    return result
