from unittest.mock import patch

from src.df_reader import load_data_from_excel


def test_load_data_from_excel_missing_file() -> None:
    with patch("pandas.read_excel") as mock_read:
        mock_read.side_effect = FileNotFoundError
        result = load_data_from_excel("non_existent_file.xlsx")
        assert result == []
