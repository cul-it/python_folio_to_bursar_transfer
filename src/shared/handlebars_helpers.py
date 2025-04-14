# beginning of file
"""
This module contains helper functions for handlebars templates.
exposed methods:
    left_pad(context, value: string, width: int, char: string) -> string:
        Left pad a value with a character to a specified width.
    right_pad(context, value: string, width: int, char: string) -> string:
        Right pad a value with a character to a specified width.
    format_date(context, value: string, format: string, import_format: boolean)
        -> string: Format a date string to a specified format.
    format_money(context, value: string) -> string: Format a number to a
        currency string with two decimal places.
Usage:
    {{left_pad <<FIELD>> 10 "0"}}
    {{right_pad <<FIELD>> 10 "0"}}
    {{format_date <<FIELD>> "%Y-%m-%d"}}
    {{format_date <<FIELD>> "%Y-%m-%d" import_format="%Y-%m-%dT%H:%M:%S.%fZ"}}
    {{format_money <<FIELD>>}}
"""
# pylint: disable=unused-argument
import logging
from datetime import date, datetime

logger = logging.getLogger(__name__)

# pylint: disable-next=unused-argument


def left_pad(context, value, width=5, char=' '):
    """
    Left pad a value with a character to a specified width. (Required by handlebars)
    :param context: The context in which the helper is called.
    :param value: The value to pad.
    :param width: The total width of the padded string. :default 5
    :param char: The character to pad with. :default ' '
    :return: The padded string.
    """
    logger.info("Running left_pad with value: %s, width: %d, char: '%s'",
                value, width, char)
    return str(value).rjust(width, char)

# pylint: disable-next=unused-argument


def right_pad(context, value, width=5, char=' '):
    """
    Right pad a value with a character to a specified width. (Required by handlebars)
    :param context: The context in which the helper is called.
    :param value: The value to pad.
    :param width: The total width of the padded string. :default 5
    :param char: The character to pad with. :default ' '
    :return: The padded string.
    """
    logger.info("Running right_pad with value: %s, width: %d, char: '%s'",
                value, width, char)
    return str(value).ljust(width, char)

# pylint: disable-next=unused-argument


def format_date(context, value, output_format='%Y-%m-%d', import_format=False):
    """
    Format a date string to a specified format.
    :param context: The context in which the helper is called. (Required by handlebars)
    :param value: The date string to format.
    :param format: The format to convert the date to. :default '%Y-%m-%d'
    :param import_format: The format to parse the date string. :default False
    :return: The formatted date string.
    """
    logger.info(
        "Running format_date with value: %s, output_format: %s, import_format: %s",
        value,
        output_format,
        import_format)
    if value.upper() == "NOW":
        wrk_date = date.today()
        logger.debug("Using current date: %s", wrk_date)
    elif import_format:
        try:
            wrk_date = datetime.strptime(value, import_format).date()
            logger.debug("Parsed date with import_format: %s", wrk_date)
        except ValueError as exc:
            logger.error(
                "Invalid date format for value: %s with import_format: %s",
                value,
                import_format,
                exc_info=True)
            raise ValueError("Invalid date format") from exc
    else:
        try:
            wrk_date = datetime.fromisoformat(value).date()
            logger.debug("Parsed date with ISO format: %s", wrk_date)
        except ValueError as exc:
            logger.error("Invalid ISO date format for value: %s",
                         value, exc_info=True)
            raise ValueError("Invalid date format") from exc
    formatted_date = wrk_date.strftime(output_format)
    logger.info("Formatted date: %s", formatted_date)
    return formatted_date

# pylint: disable-next=unused-argument


def format_money(context, value):
    """
    Format a number to a currency string with two decimal places.
    :param context: The context in which the helper is called. (Required by handlebars)
    :param value: The number to format.
    :return: The formatted currency string.
    """
    logger.info("Running format_money with value: %s", value)
    try:
        formatted_value = f"{float(value):.2f}"
        logger.info("Formatted money value: %s", formatted_value)
        return formatted_value
    except ValueError:
        logger.error("Invalid value for formatting money: %s",
                     value, exc_info=True)
        raise

# End of src/shared/handlebars_helpers.py
