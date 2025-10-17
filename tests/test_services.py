import json
from typing import Any, Dict, List, Union
from unittest.mock import Mock, patch

import pytest

from src.services import simple_search


def test_simple_search_success(transactions: List[Dict[str, str]]) -> None:
    # Тестируем правильное поведение функции
    result = simple_search("супермаркеты", transactions)
    assert len(json.loads(result)) == 2

    result = simple_search("Pskov", transactions)
    assert len(json.loads(result)) == 1


def test_simple_search_mock(transactions: List[Dict[str, str]]) -> None:
    # Тестируем правильное поведение функции при помощи Mock()
    mock_transactions = Mock()
    mock_transactions.return_value = transactions

    result = simple_search("красота", transactions)
    assert len(json.loads(result)) == 2


# Определим конкретный тип для транзакций
Transaction = Dict[str, Union[str, int, float]]

# Тестовые данные для параметризации
search_invalid_values: List[Union[int, float, list, dict, bytes, bool]] = [123, 3.14, ["список"], {"dict": 1}, True]


@pytest.mark.parametrize("search", search_invalid_values)
def test_simple_search_invalid_search(transactions: List[Transaction], search: str) -> None:
    # Тест на проверку некорректных значений поискового запроса
    with pytest.raises(ValueError) as excinfo:
        # Передаем некорректный поисковый запрос и корректные транзакции
        simple_search(search, transactions)
    assert str(excinfo.value) == "Запрос должен быть строкой"


@patch("json.dumps")
def test_simple_search_invalid_transactions_type(mock_dumps: Any) -> None:
    # Проверяем обработку неверного типа транзакций
    with pytest.raises(ValueError):
        simple_search("поиск", "не_список")  # type: ignore
