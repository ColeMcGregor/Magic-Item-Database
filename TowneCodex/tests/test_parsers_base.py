import pytest
from townecodex.parsers import base
from townecodex.parsers.csv_parser import CSVParser

def test_parsererror_is_exception():
    with pytest.raises(base.ParserError):
        raise base.ParserError("oops")

def test_choose_parser_csv():
    parser = base.choose_parser("items.csv")
    assert isinstance(parser, CSVParser)

def test_choose_parser_unsupported():
    with pytest.raises(base.ParserError):
        base.choose_parser("items.txt")
