import os
from src.df_reader import load_data_from_excel
import datetime
import json
from typing import Callable, Optional
import pandas as pd
from functools import wraps
import logging


# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def report_decorator(filename: Optional[str] = None) -> Callable:
    def decorator(func: Callable[[pd.DataFrame, str, Optional[str]], pd.DataFrame]) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> pd.DataFrame:
            result: pd.DataFrame = func(*args, **kwargs)

            if filename is None:
                report_name = f"report_{func.__name__}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            else:
                report_name = filename

            try:
                def datetime_converter(obj) -> None:
                    if isinstance(obj, pd._libs.tslibs.timestamps.Timestamp):
                        return obj.strftime("%Y-%m-%d %H:%M:%S")
                    raise TypeError

                with open(report_name, "w", encoding="utf-8") as f:
                    json.dump(
                        result.to_dict(orient="records"),
                        f,
                        ensure_ascii=False,
                        indent=4,
                        default=datetime_converter
                    )
                logging.info(f"Отчет успешно сохранен в файл: {report_name}")
            except Exception as e:
                logging.error(f"Ошибка при сохранении отчета: {str(e)}")

            return result

        return wrapper

    return decorator

@report_decorator()
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    try:
        # Обработка даты (без изменений)
        if date is None:
            end_date = datetime.now().replace(hour=0, minute=0, second=0)
        else:
            date_str = date.split()[0]
            end_date = pd.to_datetime(date_str, format="%d.%m.%Y", dayfirst=True)
            end_date = end_date.replace(hour=0, minute=0, second=0)

        start_date = end_date - pd.DateOffset(months=3)

        # Преобразуем даты в датафрейме (без изменений)
        transactions["Дата операции"] = pd.to_datetime(
            transactions["Дата операции"],
            format="%d.%m.%Y %H:%M:%S",
            dayfirst=True
        )

        # Приводим категории к нижнему регистру для поиска
        transactions['Категория_lower'] = transactions['Категория'].str.lower()
        search_term = category.lower()

        # Фильтрация с учетом частичного совпадения
        filtered_df = transactions[
            (transactions["Дата операции"] >= start_date) &
            (transactions["Дата операции"] <= end_date) &
            (transactions['Категория_lower'].str.contains(search_term, na=False))
            ]

        logging.info(f"Исходная дата: {end_date}")
        logging.info(f"Начальная дата: {start_date}")
        logging.info(f"Категория поиска: {category}")
        logging.info(f"Количество записей после фильтрации: {len(filtered_df)}")

        if not filtered_df.empty:
            result_df = (
                filtered_df.groupby(["Дата операции", "Категория"])
                .agg(
                    total_amount=("Сумма операции", "sum"),
                    transactions_count=("Сумма операции", "count")
                )
                .reset_index()
            )
            # Удаляем вспомогательный столбец
            result_df.drop(columns=['Категория_lower'], errors='ignore', inplace=True)
        else:
            logging.warning("Фильтрация вернула пустой DataFrame")
            return pd.DataFrame()

        return result_df

    except Exception as e:
        logging.error(f"Ошибка при формировании отчета: {str(e)}")
        return pd.DataFrame()





if __name__ == "__main__":
    file_path = os.path.join("..", "data", "operations.xlsx")
    df = load_data_from_excel(file_path)
    result = spending_by_category(df, "апт", '01.01.2020')
    print(result)
