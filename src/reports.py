import json
import logging
import os
from datetime import datetime, time, timedelta
from functools import wraps
from typing import Any, Callable, Optional

import pandas as pd

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def report_decorator(filename: Optional[str] = None) -> Callable:
    def decorator(func: Callable[[pd.DataFrame, str, Optional[str]], pd.DataFrame]) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> pd.DataFrame:
            result = func(*args, **kwargs)

            # Создаем путь к директории для отчетов
            report_dir = "../src/reports"
            if not os.path.exists(report_dir):
                os.makedirs(report_dir)

            if filename is None:
                report_name = f"report_{func.__name__}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            else:
                report_name = filename

            try:

                def datetime_converter(obj: object) -> str:
                    if isinstance(obj, pd._libs.tslibs.timestamps.Timestamp):
                        return obj.strftime("%Y-%m-%d %H:%M:%S")
                    raise TypeError

                # Формируем полный путь к файлу
                full_path = os.path.join(report_dir, report_name)

                with open(full_path, "w", encoding="utf-8") as f:
                    json.dump(
                        result.to_dict(orient="records"), f, ensure_ascii=False, indent=4, default=datetime_converter
                    )
                logging.info(f"Отчет успешно сохранен в файл: {full_path}")
            except Exception as e:
                logging.error(f"Ошибка при сохранении отчета: {str(e)}")

            return result

        return wrapper

    return decorator


@report_decorator()
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    # Преобразуем даты в DataFrame в правильный формат
    transactions["Дата операции"] = pd.to_datetime(transactions["Дата операции"], format="%d.%m.%Y %H:%M:%S")

    # Обработка переданной даты
    if date is None:
        end_date = datetime.now()
    else:
        try:
            # Пытаемся парсить с временем
            end_date = datetime.strptime(date, "%d.%m.%Y %H:%M:%S")
        except ValueError:
            # Если не получилось, парсим только дату
            end_date = datetime.strptime(date, "%d.%m.%Y")
            # Добавляем максимальное время дня
            end_date = datetime.combine(end_date, time(23, 59, 59))

    # Рассчитываем начальную дату (3 месяца назад)
    start_date = end_date - timedelta(days=90)
    # Приводим категории к нижнему регистру для поиска
    transactions["Категория_lower"] = transactions["Категория"].str.lower()
    search_term = category.lower()

    # Фильтрация с учетом частичного совпадения
    filtered_df = transactions[
        (transactions["Дата операции"] >= start_date)
        & (transactions["Дата операции"] <= end_date)
        & (transactions["Категория_lower"].str.contains(search_term, na=False))
    ]

    logging.info(f"Исходная дата: {end_date}")
    logging.info(f"Начальная дата: {start_date}")
    logging.info(f"Категория поиска: {category}")
    logging.info(f"Количество записей после фильтрации: {len(filtered_df)}")

    if not filtered_df.empty:
        result_df = (
            filtered_df.groupby(["Дата операции", "Категория"])
            .agg(ИТОГО=("Сумма операции", "sum"), ВСЕГО=("Сумма операции", "count"))
            .reset_index()
        )
        # Форматируем дату обратно в строку
        result_df["Дата операции"] = result_df["Дата операции"].dt.strftime("%d.%m.%Y %H:%M:%S")
        # Округление значений
        result_df["ИТОГО"] = result_df["ИТОГО"].round(2)
        result_df["ВСЕГО"] = result_df["ВСЕГО"].round(2)

        # Удаляем вспомогательный столбец
        result_df.drop(columns=["Категория_lower"], errors="ignore", inplace=True)

        # Создаем итоговую строку
        total_spending = filtered_df["Сумма операции"].sum().round(2)
        total_transactions = filtered_df.shape[0]

        total_row = pd.DataFrame(
            {
                "Дата операции": ["Итоговая"],
                "Категория": ["сумма"],
                "ИТОГО": [total_spending],
                "ВСЕГО": [total_transactions],
            }
        )

        # Добавляем итоговую строку в конец
        result_df = pd.concat([result_df, total_row], ignore_index=True)

        print(f"Минимальная допустимая дата operations.xlsx: {transactions['Дата операции'].min()}")
        print(f"Максимальная допустимая дата operations.xlsx: {transactions['Дата операции'].max()}")
        return result_df
    else:
        logging.warning("Фильтрация вернула пустой DataFrame")
        return pd.DataFrame()
