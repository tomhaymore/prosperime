from django import template
register = template.Library()

import datetime

@register.filter(name="months_difference")
def months_difference(value, arg):

    if arg == "Current":
        return 0
    else:
        return (12 * (value.year - arg.year)) + (value.month - arg.month)
