from datetime import date, timedelta, datetime

def left_pad(context, value, width=5, char=' '):
    return str(value).rjust(width, char)

def right_pad(context, value, width=5, char=' '):
    return str(value).ljust(width, char)

def format_date(context, value, format='%Y-%m-%d', import_format=False):
    if value.upper() == "NOW":
        wrk_date = date.today()
    elif import_format:
        try:
            wrk_date = datetime.strptime(value, import_format).date()
        except ValueError:
            raise ValueError("Invalid date format")
    else:
        try:
            wrk_date = datetime.fromisoformat(value).date()
        except ValueError:
            raise ValueError("Invalid date format")
    return wrk_date.strftime(format)

def format_money(context, value):
    return f"{float(value):.2f}"