import json
import logging
import os

import pandas as pd

from src.utils import filter_by_range, get_exchange_rates, get_expenses_summary, get_incomes_summary, get_sp500_quotes

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)


def get_events(date_str: str, range_type: str = "M") -> str:
    """
    Главная функция страницы «События».
    """
    logger.info(f"Получение событий на дату {date_str}, диапазон {range_type}")
    file_path = os.path.join("..", "data", "operations.xlsx")
    try:

        df = pd.read_excel(file_path)

        # Фильтрация дат
        logger.info(f"Данные считаны: {len(df)} записей")
        df_filtered = filter_by_range(df, date_str, range_type)

        # Формирование данных
        expenses = get_expenses_summary(df_filtered)
        incomes = get_incomes_summary(df_filtered)
        exchange_rates = get_exchange_rates(date_str)
        sp500_quotes = get_sp500_quotes(date_str)

        result = {
            "Расходы": expenses,
            "Поступления": incomes,
            "Курс валют": exchange_rates,
            "Стоимость акций S&P 500": sp500_quotes,
        }
        logger.info("JSON-ответ сформирован")
        return json.dumps(result, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Ошибка формирования событий: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)


if __name__ == "__main__":
    print(get_events("20-05-2019"))
