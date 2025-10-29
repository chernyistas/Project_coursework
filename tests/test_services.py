import json
from typing import Any, Dict, List, Union
from unittest.mock import Mock, patch

import pytest

from src.services import (
    filter_transfers_to_physical_persons,
    is_physical_person_transfer,
    search_physical_person_transfers,
    simple_search,
)


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
        simple_search(search, transactions)
    assert str(excinfo.value) == "Запрос должен быть строкой"


@patch("json.dumps")
def test_simple_search_invalid_transactions_type(mock_dumps: Any) -> None:
    # Проверяем обработку неверного типа транзакций
    with pytest.raises(ValueError):
        simple_search("поиск", "не_список")  # type: ignore


def test_is_physical_person_transfer() -> None:
    # Корректные форматы
    assert is_physical_person_transfer("Иванов И.")
    assert is_physical_person_transfer("Петрова А.")
    assert is_physical_person_transfer("Сидоров К.")

    # Некорректные форматы
    assert not is_physical_person_transfer("Иванов Иван")
    assert not is_physical_person_transfer("Иванов")
    assert not is_physical_person_transfer("И. Иванов")
    assert not is_physical_person_transfer("иванов и.")
    assert not is_physical_person_transfer("Иванов И.П.")
    assert not is_physical_person_transfer("123 И.")


def test_filter_transfers_to_physical_persons(test_physical_transactions: list[dict[Any, Any]]) -> None:
    # Тест перевода физ лиц
    result = filter_transfers_to_physical_persons(test_physical_transactions)
    assert len(result) == 2
    assert result[0]["Описание"] == "Иванов И."


def test_empty_input() -> None:
    # Тест на пустой ввод поиска транзакций физ лиц
    result = search_physical_person_transfers([])
    data = json.loads(result)
    assert data["Итого"] == 0
    assert len(data["transactions"]) == 0


def test_mock_no_transactions() -> None:
    # Тест с пустым списком транзакций
    with patch("src.services.search_physical_person_transfers") as mock_search:
        mock_search.return_value = []

        result = search_physical_person_transfers([])
        data = json.loads(result)

        assert data["Итого"] == 0
        assert len(data["transactions"]) == 0


def test_mock_with_empty_input() -> None:
    # Тест на вызов без аргументов
    with patch("src.services.search_physical_person_transfers"):

        result = search_physical_person_transfers("transactions")  # type: ignore
        data = json.loads(result)

        assert data["Итого"] == 0
        assert len(data["transactions"]) == 0


def test_mock_with_invalid_input() -> None:
    # Тестируем с некорректным вводом
    with patch("src.services.search_physical_person_transfers"):

        result = search_physical_person_transfers("неверный_тип")  # type: ignore
        data = json.loads(result)

        assert data == {"Итого": 0, "transactions": []}
