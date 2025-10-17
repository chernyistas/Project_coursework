from src.utils import load_data_from_exel
from unittest.mock import patch
import pandas as pd
def test_load_data_from_exel_missing_file()-> None:
    with patch('pandas.read_excel') as mock_read:
        mock_read.side_effect = FileNotFoundError
        result = load_data_from_exel('non_existent_file.xlsx')
        assert result == []