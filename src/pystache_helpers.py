# import pystache
from datetime import date, timedelta, datetime

def left_pad(value, width=5, char=' '):
    return str(value).rjust(width, char)

def right_pad(value, width=5, char=' '):
    return str(value).ljust(width, char)

def format_date(value, format='%Y-%m-%d'):
    if value.upper() == "NOW":
        wrk_date = date.today()
    else:
        try:
            wrk_date = datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            raise ValueError("Invalid date format. Use 'YYYY-MM-DD'.")
    return wrk_date.strftime(format)

# Custom renderer class to include the padding functions
class CustomRenderer(pystache.Renderer):
    def __init__(self, *args, **kwargs):
        super(CustomRenderer, self).__init__(*args, **kwargs)
        self.helpers = {
            'left_pad': left_pad,
            'right_pad': right_pad,
            'format_date': format_date
        }

    def render(self, template, context=None, **kwargs):
        if context is None:
            context = {}
        context.update(self.helpers)
        return super(CustomRenderer, self).render(template, context, **kwargs)