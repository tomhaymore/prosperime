from django import template
register = template.Library()

@register.filter(name="rangify")
def rangify(value):
    return range(value)


