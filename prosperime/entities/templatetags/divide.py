from django import template
register = template.Library()

@register.filter(name="divide")
def divide(value, arg):
    return value/arg;
