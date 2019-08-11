from django import template

register = template.Library()


@register.filter(name='sub')
def sub(value1, value2):
    return int(value1) - int(value2)
