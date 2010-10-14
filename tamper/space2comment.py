import re

from lib.core.convert import urldecode
from lib.core.convert import urlencode

"""
' ' -> /**/ (e.g., SELECT id FROM users->SELECT/**/id/**/FROM users)
"""
#TODO: only do it for deepness = 0 regarding '"
def tamper(place, value):
    if value:
        if place != "URI":
            value = urldecode(value)
        value = value.replace(" ", "/**/")
        if place != "URI":
            value = urlencode(value)
    return value
