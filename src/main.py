import json
import logging
import os
from datetime import datetime

import pandas as pd

from src.df_reader import load_and_convert_excel_to_dict
from src.reports import spending_by_category
from src.services import search_physical_person_transfers, simple_search
from src.views import get_events

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    print("\nДобро пожаловать в систему анализа транзакций!")
    print("Доступные команды:")
    print("1. Простой поиск по описанию или категории")
    print("2. Поиск переводов физическим лицам")
    print("3. Отчет по тратам по категории")
    print("4. Итог по всем финансовым данным — расходы, доходы, валюты, акции (страница «События»)")
    print("0. Выход")

    try:
        # Загрузка данных из Excel
        file_path = os.path.join("../data", "operations.xlsx")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл {file_path} не найден")

        df = pd.read_excel(file_path)
        transactions_list = load_and_convert_excel_to_dict(file_path)

        while True:
            choice = input("\nВыберите действие (0-4): ").strip()

            if choice == "0":
                print("До свидания!")
                break

            elif choice == "1":
                search = input("Введите строку для поиска: ").strip()
                result = simple_search(search, transactions_list)
                print("\nРезультаты поиска:")
                print(result)

            elif choice == "2":
                result = search_physical_person_transfers(transactions_list)
                print("\nПереводы физическим лицам:")
                print(result)

            elif choice == "3":
                category = input("Введите категорию: ").strip()
                date = input("Введите дату (ДД.ММ.ГГГГ) или Enter для текущей даты: ").strip()
                if not date:
                    date = datetime.now().strftime("%d.%m.%Y")
                result = spending_by_category(df, category, date)
                print("\nОтчет по тратам:")
                print(result)

            elif choice == "4":
                print("\n=== Финансовые события ===")
                date_str = input("Введите дату (ДД.ММ.ГГГГ или ГГГГ-ММ-ДД). По умолчанию текущая дата: ").strip()
                range_type = (
                    input("Введите диапазон (W — неделя, M — месяц, Y — год, ALL — всё время). Enter — месяц: ")
                    .strip()
                    .upper()
                )

                if not date_str:
                    date_str = datetime.now().strftime("%d.%m.%Y")
                if not range_type:
                    range_type = "M"

                logger.info(f"Запуск get_events для даты {date_str}, диапазон {range_type}")
                result_json = get_events(date_str, range_type)

                try:
                    result = json.loads(result_json)
                except json.JSONDecodeError:
                    result = {"Ошибка": "Не удалось преобразовать результат в JSON."}  # type: ignore[assignment]

                print("\nИтоговый отчет:")
                print(json.dumps(result, ensure_ascii=False, indent=4))

            else:
                print("Неверный выбор. Попробуйте снова.")

    except FileNotFoundError as fnf_error:
        logger.error(f"Файл не найден: {fnf_error}")
        print(f"Ошибка: {fnf_error}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        print(f"Ошибка выполнения: {e}")


if __name__ == "__main__":
    main()
