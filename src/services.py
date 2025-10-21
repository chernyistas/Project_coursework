import json
import logging
import os
import re
from typing import Dict, List

from src.df_reader import load_and_convert_excel_to_dict

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def simple_search(search: str, transactions: list[dict]) -> str:
    """Поиск транзакций по ключевому слову в описании или категории"""
    # Проверка входных данных
    if not isinstance(search, str):
        logging.error("Неверный тип запроса")
        raise ValueError("Запрос должен быть строкой")

    if not isinstance(transactions, list):
        logging.error("Неверный тип данных транзакций")
        raise ValueError("Транзакции должны быть списком словарей")

    try:
        logging.info(f"Начат поиск по запросу: {search}")

        # Приведение запроса к нижнему регистру
        search_term = search.lower()

        # Фильтрация транзакций с проверкой типов
        results = [
            transaction
            for transaction in transactions
            if isinstance(transaction, dict)
            and (
                (
                    isinstance(transaction.get("Описание"), str)
                    and search_term in transaction.get("Описание", "").lower()
                )
                or (
                    isinstance(transaction.get("Категория"), str)
                    and search_term in transaction.get("Категория", "").lower()
                )
            )
        ]

        logging.info(f"Найдено {len(results)} совпадений")

        # Конвертация в JSON
        return json.dumps(results, ensure_ascii=False, indent=4, sort_keys=True)

    except Exception as e:
        logging.error(f"Произошла ошибка: {str(e)}")
        return json.dumps({"error": "Произошла ошибка при обработке запроса"})


def is_physical_person_transfer(description: str) -> bool:
    """
    Проверяет, соответствует ли описание транзакции формату перевода физлицу
    """
    # Регулярное выражение для поиска имени и первой буквы фамилии с точкой
    pattern = r"^[А-Я][а-я]+\s[А-Я]\.$"
    return bool(re.match(pattern, description))


def filter_transfers_to_physical_persons(transactions: List[Dict]) -> List[Dict]:
    """
    Фильтрует транзакции по критериям переводов физлицам
    """
    filtered_transactions = []

    for transaction in transactions:
        try:
            # Проверяем категорию и формат описания
            if transaction.get("Категория") == "Переводы" and is_physical_person_transfer(
                transaction.get("Описание", "")
            ):
                filtered_transactions.append(transaction)
        except Exception as e:
            logging.error(f"Ошибка при обработке транзакции: {e}")

    return filtered_transactions


def search_physical_person_transfers(transactions: List[Dict]) -> str:
    """
    Основная функция поиска переводов физлицам с формированием JSON-ответа
    """
    try:
        # Фильтруем транзакции
        filtered_transactions = filter_transfers_to_physical_persons(transactions)

        # Формируем JSON-ответ
        result = {"transactions": filtered_transactions, "count": len(filtered_transactions)}

        logging.info(f"Найдено {len(filtered_transactions)} переводов физлицам")
        return json.dumps(result, ensure_ascii=False, indent=4)

    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")
        return json.dumps({"error": str(e)})


# Пример использования
if __name__ == "__main__":
    file_path = os.path.join("..", "data", "operations.xlsx")
    df_dict = load_and_convert_excel_to_dict(file_path)
    print(search_physical_person_transfers(df_dict))
