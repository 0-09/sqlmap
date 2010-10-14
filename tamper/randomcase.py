#!/usr/bin/env python

# Copyright (c) 2006-2010 sqlmap project (http://sqlmap.sourceforge.net/)
# See the file doc/COPYING for copying permission.

import re
import string

from lib.core.common import randomRange
from lib.core.convert import urldecode
from lib.core.convert import urlencode
from lib.core.data import kb

"""
value -> chars from value with random case (e.g., INSERT->InsERt)
"""
def tamper(place, value):
    retVal = value

    if value:
        if place != "URI":
            retVal = urldecode(retVal)

        for match in re.finditer(r"[A-Za-z_]+", retVal):
            word = match.group()

            if word.upper() in kb.keywords:
                newWord = str()

                for i in xrange(len(word)):
                    newWord += word[i].upper() if randomRange(0,1) else word[i].lower()

                retVal = retVal.replace(word, newWord)

        if place != "URI":
            retVal = urlencode(retVal)

    return retVal
