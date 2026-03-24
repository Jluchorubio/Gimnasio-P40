import os
from django import template

register = template.Library()


@register.filter
def filename(path):
    if not path:
        return ""
    return os.path.basename(path)


@register.filter
def fileext(path):
    if not path:
        return ""
    _, ext = os.path.splitext(path)
    return ext.replace(".", "").upper()
