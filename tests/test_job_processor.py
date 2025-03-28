import pytest
from unittest.mock import patch
from datetime import date
from src.job_processor import JobProcessor


@pytest.fixture
def processor():
    # Initialize the JobProcessor instance
    return JobProcessor()


@patch("src.job_processor.date")
def test_check_days(mock_date, processor):
    # Mock today's date to be Sunday (0)
    mock_date.today.return_value = date(2025, 3, 30)  # Sunday
    mock_date.strftime = date.strftime

    # Test with run_days as a list
    job = {"run_days": [0, 1, 4]}
    assert processor._JobProcessor__check_days(job) is True

    # Test with run_days not matching
    job = {"run_days": [1, 2, 3]}
    assert processor._JobProcessor__check_days(job) is False

    # Test with no run_days
    job = {}
    assert processor._JobProcessor__check_days(job) is True


@patch("src.job_processor.date")
def test_check_month(mock_date, processor):
    # Mock today's date to be March (03)
    mock_date.today.return_value = date(2025, 3, 30)
    mock_date.strftime = date.strftime

    # Test with run_on_month as "EVERY"
    job = {"run_on_month": "EVERY"}
    assert processor._JobProcessor__check_month(job) is True

    # Test with run_on_month as "ODD"
    job = {"run_on_month": "ODD"}
    assert processor._JobProcessor__check_month(job) is True

    # Test with run_on_month as "EVEN"
    job = {"run_on_month": "EVEN"}
    assert processor._JobProcessor__check_month(job) is False

    # Test with run_on_month as a list
    job = {"run_on_month": [3, 4]}
    assert processor._JobProcessor__check_month(job) is True

    # Test with run_on_month not matching
    job = {"run_on_month": [4, 5]}
    assert processor._JobProcessor__check_month(job) is False


@patch("src.job_processor.date")
def test_check_day(mock_date, processor):
    # Mock today's date to be the 30th
    mock_date.today.return_value = date(2025, 3, 30)
    mock_date.strftime = date.strftime

    # Test with run_on_day as "EVERY"
    job = {"run_on_day": "EVERY"}
    assert processor._JobProcessor__check_day(job) is True

    # Test with run_on_day as "ODD"
    job = {"run_on_day": "ODD"}
    assert processor._JobProcessor__check_day(job) is False

    # Test with run_on_day as "EVEN"
    job = {"run_on_day": "EVEN"}
    assert processor._JobProcessor__check_day(job) is True

    # Test with run_on_day as "LAST"
    job = {"run_on_day": "LAST"}
    assert processor._JobProcessor__check_day(job) is False

    # Test with run_on_day as "FIRST"
    job = {"run_on_day": "FIRST"}
    assert processor._JobProcessor__check_day(job) is False

    # Test with run_on_day as "WEEKDAY"
    job = {"run_on_day": "WEEKDAY"}
    assert processor._JobProcessor__check_day(job) is False

    # Test with run_on_day as "WEEKEND"
    job = {"run_on_day": "WEEKEND"}
    assert processor._JobProcessor__check_day(job) is True

    # Test with run_on_day as a list
    job = {"run_on_day": [30, 31]}
    assert processor._JobProcessor__check_day(job) is True

    # Test with run_on_day not matching
    job = {"run_on_day": [29]}
    assert processor._JobProcessor__check_day(job) is False

    mock_date.today.return_value = date(2025, 3, 31)
    mock_date.strftime = date.strftime

    # Test with run_on_day as "LAST"
    job = {"run_on_day": "LAST"}
    assert processor._JobProcessor__check_day(job) is True

    mock_date.today.return_value = date(2025, 3, 1)
    mock_date.strftime = date.strftime

    # Test with run_on_day as "FIRST"
    job = {"run_on_day": "FIRST"}
    assert processor._JobProcessor__check_day(job) is True

    mock_date.today.return_value = date(2025, 3, 26)
    mock_date.strftime = date.strftime
    # Test with run_on_day as "WEEKDAY"
    job = {"run_on_day": "WEEKDAY"}
    assert processor._JobProcessor__check_day(job) is True

    # Test with run_on_day as "WEEKEND"
    job = {"run_on_day": "WEEKEND"}
    assert processor._JobProcessor__check_day(job) is False
