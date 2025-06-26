from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, 1)

@register.simple_tag
def total_price(items, quantities):
    total = 0
    for item in items:
        total += item.price * quantities.get(item.id, 1)
    return total