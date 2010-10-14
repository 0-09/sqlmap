import re
import string

from lib.core.common import randomRange
from lib.core.convert import urldecode
from lib.core.convert import urlencode
from lib.core.data import kb

"""
value -> value with inserted random blanks (e.g., INSERT->IN/**/S/**/ERT)
"""
def tamper(place, value):
    retVal = value
    if value:
        if place != "URI":
            retVal = urldecode(retVal)

        for match in re.finditer(r"[A-Za-z_]+", retVal):
            word = match.group()

            if len(word) < 2:
                continue

            if word.upper() in kb.keywords:
                newWord = word[0]
                for i in xrange(1, len(word) - 1):
                    newWord += "%s%s" % ("/**/" if randomRange(0,1) else "", word[i])
                newWord += word[-1]
                retVal = retVal.replace(word, newWord)

        if place != "URI":
            retVal = urlencode(retVal)
    return retVal
