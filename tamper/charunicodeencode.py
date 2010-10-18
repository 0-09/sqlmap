#!/usr/bin/env python

"""
$Id: charencode.py 2035 2010-10-16 21:33:15Z inquisb $

Copyright (c) 2006-2010 sqlmap developers (http://sqlmap.sourceforge.net/)
See the file 'doc/COPYING' for copying permission
"""

import string

from lib.core.exception import sqlmapUnsupportedFeatureException

def tamper(place, value):
    """
    Replaces value with urlencode of non-encoded chars in value
    Example: 'SELECT%20FIELD%20FROM%20TABLE' becomes '%u0053%u0045%u004c%u0045%u0043%u0054%u0020%u0046%u0049%u0045%u004c%u0044%u0020%u0046%u0052%u004f%u004d%u0020%u0054%u0041%u0042%u004c%u0045'
    """

    retVal = value

    if value:
        if place != "URI":
            retVal = ""
            i = 0

            while i < len(value):
                if value[i] == '%' and (i < len(value) - 2) and value[i+1] in string.hexdigits and value[i+2] in string.hexdigits:
                    retVal += value[i:i+3]
                    i += 3
                else:
                    retVal += '%%u00%X' % ord(value[i])
                    i += 1
        else:
            raise sqlmapUnsupportedFeatureException, "can't use tamper script '%s' with 'URI' type injections" % __name__

    return retVal
