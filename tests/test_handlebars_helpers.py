from datetime import date
import pytest
from src.shared.handlebars_helpers import left_pad, right_pad, format_date, format_money

def test_left_pad():
    # Test with default padding
    assert left_pad(None, "123", 5) == "  123"
    # Test with custom padding character
    assert left_pad(None, "123", 5, '0') == "00123"
    # Test with no padding needed
    assert left_pad(None, "12345", 5) == "12345"
    # Test with empty value
    assert left_pad(None, "", 5) == "     "

def test_right_pad():
    # Test with default padding
    assert right_pad(None, "123", 5) == "123  "
    # Test with custom padding character
    assert right_pad(None, "123", 5, '0') == "12300"
    # Test with no padding needed
    assert right_pad(None, "12345", 5) == "12345"
    # Test with empty value
    assert right_pad(None, "", 5) == "     "

def test_format_date():
    # Test with "NOW"
    assert format_date(None, "NOW") == date.today().strftime('%Y-%m-%d')
    # Test with ISO format date
    assert format_date(None, "2025-03-27") == "2025-03-27"
    # Test with custom import format
    assert format_date(None, "03/27/2025", "%Y-%m-%d", "%m/%d/%Y") == "2025-03-27"
    # Test with invalid date format
    with pytest.raises(ValueError, match="Invalid date format"):
        format_date(None, "invalid-date")
    # Test with invalid import format
    with pytest.raises(ValueError, match="Invalid date format"):
        format_date(None, "03-27-2025", "%Y-%m-%d", "%m/%d/%Y")

def test_format_money():
    # Test with integer value
    assert format_money(None, 123) == "123.00"
    # Test with float value
    assert format_money(None, 123.456) == "123.46"
    # Test with string value
    assert format_money(None, "123.4") == "123.40"
    # Test with invalid value
    with pytest.raises(ValueError):
        format_money(None, "invalid")