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

from datetime import date, datetime

#pylint: disable-next=unused-argument
def left_pad(context, value, width=5, char=' '):
    """
    Left pad a value with a character to a specified width. (Required by handlebars)
    :param context: The context in which the helper is called.
    :param value: The value to pad.
    :param width: The total width of the padded string. :default 5
    :param char: The character to pad with. :default ' '
    :return: The padded string.
    """
    return str(value).rjust(width, char)

#pylint: disable-next=unused-argument
def right_pad(context, value, width=5, char=' '):
    """
    Right pad a value with a character to a specified width. (Required by handlebars)
    :param context: The context in which the helper is called.
    :param value: The value to pad.
    :param width: The total width of the padded string. :default 5
    :param char: The character to pad with. :default ' '
    :return: The padded string.
    """
    return str(value).ljust(width, char)

#pylint: disable-next=unused-argument
def format_date(context, value, output_format='%Y-%m-%d', import_format=False):
    """
    Format a date string to a specified format.
    :param context: The context in which the helper is called. (Required by handlebars)
    :param value: The date string to format.
    :param format: The format to convert the date to. :default '%Y-%m-%d'
    :param import_format: The format to parse the date string. :default False
    :return: The formatted date string.
    """
    if value.upper() == "NOW":
        wrk_date = date.today()
    elif import_format:
        try:
            wrk_date = datetime.strptime(value, import_format).date()
        except ValueError as exc:
            raise ValueError("Invalid date format") from exc
    else:
        try:
            wrk_date = datetime.fromisoformat(value).date()
        except ValueError as exc:
            raise ValueError("Invalid date format") from exc
    return wrk_date.strftime(output_format)

#pylint: disable-next=unused-argument
def format_money(context, value):
    """
    Format a number to a currency string with two decimal places.
    :param context: The context in which the helper is called. (Required by handlebars)
    :param value: The number to format.
    :return: The formatted currency string.
    """
    return f"{float(value):.2f}"

# End of src/shared/handlebars_helpers.py
