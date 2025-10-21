import logging
import os

import pandas as pd

from src.df_reader import load_and_convert_excel_to_dict
from src.reports import spending_by_category
from src.services import search_physical_person_transfers, simple_search

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def main() -> None:
    print("\nДобро пожаловать в систему анализа транзакций!")
    print("Доступные команды:")
    print("1. Простой поиск по описанию или категории")
    print("2. Поиск переводов физическим лицам")
    print("3. Отчет по тратам по категории")
    print("0. Выход")

    try:
        # Загрузка данных из Excel
        file_path = os.path.join("data", "operations.xlsx")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл {file_path} не найден")

        df = pd.read_excel(file_path)
        # Конвертируем датафрейм в список словарей для поиска
        transactions_list = load_and_convert_excel_to_dict(file_path)

        while True:
            try:
                choice = input("\nВыберите действие (0-3): ")

                if choice == "0":
                    print("До свидания!")
                    break

                elif choice == "1":
                    search = input("Введите строку для поиска: ")
                    result = simple_search(search, transactions_list)
                    print("\nРезультаты поиска:")
                    print(result)

                elif choice == "2":
                    result = search_physical_person_transfers(transactions_list)
                    print("\nПереводы физическим лицам:")
                    print(result)

                elif choice == "3":
                    category = input("Введите категорию: ")
                    # Минимальная допустимая дата operations.xlsx: 2018-01-01 12:49:53
                    # Максимальная допустимая дата operations.xlsx: 2021-12-31 16:44:00
                    date = input("Введите дату (ДД.ММ.ГГГГ) или нажмите Enter для текущей даты: ")
                    result = spending_by_category(df, category, date)
                    print("\nОтчет по тратам:")
                    print(result)

                else:
                    print("Неверный выбор. Попробуйте снова.")

            except Exception as e:
                logging.error(f"Произошла ошибка: {str(e)}")
                print("Произошла ошибка. Попробуйте еще раз.")

    except FileNotFoundError as fnf_error:
        logging.error(f"Файл не найден: {fnf_error}")
        print(f"Ошибка: {fnf_error}")


if __name__ == "__main__":
    main()
