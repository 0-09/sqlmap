#!/usr/bin/env python

"""
$Id$

Copyright (c) 2006-2010 sqlmap developers (http://sqlmap.sourceforge.net/)
See the file 'doc/COPYING' for copying permission
"""

import re
import socket
import time

from difflib import SequenceMatcher

from lib.core.agent import agent
from lib.core.common import getFilteredPageContent
from lib.core.common import getUnicode
from lib.core.common import preparePageForLineComparison
from lib.core.common import randomInt
from lib.core.common import randomStr
from lib.core.common import readInput
from lib.core.common import showStaticWords
from lib.core.common import DynamicContentItem
from lib.core.convert import md5hash
from lib.core.convert import urlencode
from lib.core.data import conf
from lib.core.data import kb
from lib.core.data import logger
from lib.core.data import paths
from lib.core.exception import sqlmapConnectionException
from lib.core.exception import sqlmapNoneDataException
from lib.core.exception import sqlmapUserQuitException
from lib.core.exception import sqlmapSilentQuitException
from lib.core.session import setString
from lib.core.session import setRegexp
from lib.request.connect import Connect as Request

def checkSqlInjection(place, parameter, value, parenthesis):
    """
    This function checks if the GET, POST, Cookie, User-Agent
    parameters are affected by a SQL injection vulnerability and
    identifies the type of SQL injection:

      * Unescaped numeric injection
      * Single quoted string injection
      * Double quoted string injection
    """

    logic = conf.logic
    randInt = randomInt()
    randStr = randomStr()
    prefix = ""
    postfix = ""

    if conf.prefix or conf.postfix:
        if conf.prefix:
            prefix = conf.prefix

        if conf.postfix:
            postfix = conf.postfix

    for case in kb.injections.root.case:
        positive = case.test.positive
        negative = case.test.negative

        if not prefix and not postfix and case.name == "custom":
            continue

        infoMsg  = "testing %s (%s) injection " % (case.desc, logic)
        infoMsg += "on %s parameter '%s'" % (place, parameter)
        logger.info(infoMsg)

        payload = agent.payload(place, parameter, value, positive.format % eval(positive.params))
        trueResult = Request.queryPage(payload, place)

        if trueResult:
            payload = agent.payload(place, parameter, value, negative.format % eval(negative.params))

            falseResult = Request.queryPage(payload, place)

            if not falseResult:
                infoMsg  = "%s parameter '%s' is %s (%s) injectable " % (place, parameter, case.desc, logic)
                infoMsg += "with %d parenthesis" % parenthesis
                logger.info(infoMsg)
                return case.name

    return None

def heuristicCheckSqlInjection(place, parameter, value):
    prefix = ""
    postfix = ""

    if conf.prefix or conf.postfix:
        if conf.prefix:
            prefix = conf.prefix

        if conf.postfix:
            postfix = conf.postfix

    payload = "%s%s%s" % (prefix, randomStr(length=10, alphabet=['"', '\'', ')', '(']), postfix)

    if place == "URI":
        payload = conf.paramDict[place][parameter].replace('*', payload)

    Request.queryPage(payload, place)
    result = kb.lastErrorPage and kb.lastErrorPage[0]==kb.lastRequestUID

    infoMsg  = "(error based) heuristics shows that %s " % place
    infoMsg += "parameter '%s' is " % parameter

    if result:
        infoMsg += "injectable (possible DBMS: %s)" % kb.htmlFp[-1]
        logger.info(infoMsg)
    else:
        infoMsg += "not injectable"
        logger.warning(infoMsg)

def checkDynParam(place, parameter, value):
    """
    This function checks if the url parameter is dynamic. If it is
    dynamic, the content of the page differs, otherwise the
    dynamicity might depend on another parameter.
    """

    infoMsg = "testing if %s parameter '%s' is dynamic" % (place, parameter)
    logger.info(infoMsg)

    randInt = randomInt()
    payload = agent.payload(place, parameter, value, getUnicode(randInt))
    dynResult1 = Request.queryPage(payload, place)

    if True == dynResult1:
        return False

    infoMsg = "confirming that %s parameter '%s' is dynamic" % (place, parameter)
    logger.info(infoMsg)

    payload = agent.payload(place, parameter, value, "'%s" % randomStr())
    dynResult2 = Request.queryPage(payload, place)

    payload = agent.payload(place, parameter, value, "\"%s" % randomStr())
    dynResult3 = Request.queryPage(payload, place)

    condition  = True != dynResult2
    condition |= True != dynResult3

    return condition

def checkDynamicContent(*pages):
    """
    This function checks if the provided pages have dynamic content. If they
    are dynamic, their content differs at specific lines.
    """

    infoMsg = "searching for dynamic content"
    logger.info(infoMsg)

    for i in xrange(len(pages)):
        firstPage = pages[i]
        linesFirst = preparePageForLineComparison(firstPage)
        pageLinesNumber = len(linesFirst)

        for j in xrange(i+1, len(pages)):
            secondPage = pages[j]
            linesSecond = preparePageForLineComparison(secondPage)

            if pageLinesNumber == len(linesSecond):
                for k in xrange(0, pageLinesNumber):
                    if (linesFirst[k] != linesSecond[k]):
                        item = DynamicContentItem(k, pageLinesNumber, \
                            linesFirst[k-1] if k > 0 else None, \
                            linesFirst[k+1] if k < pageLinesNumber - 1 else None)

                        found = None

                        for other in kb.dynamicContent:
                            found = True

                            if other.pageTotal == item.pageTotal:
                                if isinstance(other.lineNumber, int):
                                    if other.lineNumber == item.lineNumber - 1:
                                        other.lineNumber = [other.lineNumber, item.lineNumber]
                                        other.lineContentAfter = item.lineContentAfter
                                        break

                                    elif other.lineNumber == item.lineNumber + 1:
                                        other.lineNumber = [item.lineNumber, other.lineNumber]
                                        other.lineContentBefore = item.lineContentBefore
                                        break

                                elif item.lineNumber - 1 == other.lineNumber[-1]:
                                    other.lineNumber.append(item.lineNumber)
                                    other.lineContentAfter = item.lineContentAfter
                                    break

                                elif item.lineNumber + 1 == other.lineNumber[0]:
                                    other.lineNumber.insert(0, item.lineNumber)
                                    other.lineContentBefore = item.lineContentBefore
                                    break

                            found = False

                        if not found:
                            kb.dynamicContent.append(item)

    if kb.dynamicContent:
        infoMsg = "found probably removable dynamic lines"
        logger.info(infoMsg)

def checkStability():
    """
    This function checks if the URL content is stable requesting the
    same page two times with a small delay within each request to
    assume that it is stable.

    In case the content of the page differs when requesting
    the same page, the dynamicity might depend on other parameters,
    like for instance string matching (--string).
    """

    infoMsg = "testing if the url is stable, wait a few seconds"
    logger.info(infoMsg)

    firstPage, _ = Request.queryPage(content=True)
    time.sleep(1)
    secondPage, _ = Request.queryPage(content=True)

    condition = (firstPage == secondPage)

    if condition:
        if firstPage:
            conf.md5hash = md5hash(firstPage)
            logMsg  = "url is stable"
            logger.info(logMsg)
        else:
            errMsg  = "there was an error checking the stability of page "
            errMsg += "because of lack of content. please check the "
            errMsg += "page request results (and probable errors) by "
            errMsg += "using higher verbosity levels"
            raise sqlmapNoneDataException, errMsg

    elif not condition:
        warnMsg  = "url is not stable, sqlmap will base the page "
        warnMsg += "comparison on a sequence matcher. If no dynamic nor "
        warnMsg += "injectable parameters are detected, or in case of "
        warnMsg += "junk results, refer to user's manual paragraph "
        warnMsg += "'Page comparison' and provide a string or regular "
        warnMsg += "expression to match on"
        logger.warn(warnMsg)

        message = "how do you want to proceed? [C(ontinue)/s(tring)/r(egex)/q(uit)] "
        test = readInput(message, default="C")

        if test and test[0] in ("q", "Q"):
            raise sqlmapUserQuitException

        elif test and test[0] in ("s", "S"):
            showStaticWords(firstPage, secondPage)

            message = "please enter value for parameter 'string': "
            test = readInput(message)

            if test:
                conf.string = test
            else:
                raise sqlmapSilentQuitException

        elif test and test[0] in ("r", "R"):
            message = "please enter value for parameter 'regex': "
            test = readInput(message)

            if test:
                conf.regex = test
            else:
                raise sqlmapSilentQuitException
        else:
            checkDynamicContent(firstPage, secondPage)

    return condition

def checkString():
    if not conf.string:
        return True

    condition = (
                  kb.resumedQueries.has_key(conf.url) and
                  kb.resumedQueries[conf.url].has_key("String") and
                  kb.resumedQueries[conf.url]["String"][:-1] == conf.string
                )

    if condition:
        return True

    infoMsg  = "testing if the provided string is within the "
    infoMsg += "target URL page content"
    logger.info(infoMsg)

    page, _ = Request.queryPage(content=True)

    if conf.string in page:
        setString()
        return True
    else:
        errMsg  = "you provided '%s' as the string to " % conf.string
        errMsg += "match, but such a string is not within the target "
        errMsg += "URL page content, please provide another string."
        logger.error(errMsg)

        return False

def checkRegexp():
    if not conf.regexp:
        return True

    condition = (
                  kb.resumedQueries.has_key(conf.url) and
                  kb.resumedQueries[conf.url].has_key("Regular expression") and
                  kb.resumedQueries[conf.url]["Regular expression"][:-1] == conf.regexp
                )

    if condition:
        return True

    infoMsg  = "testing if the provided regular expression matches within "
    infoMsg += "the target URL page content"
    logger.info(infoMsg)

    page, _ = Request.queryPage(content=True)

    if re.search(conf.regexp, page, re.I | re.M):
        setRegexp()
        return True
    else:
        errMsg  = "you provided '%s' as the regular expression to " % conf.regexp
        errMsg += "match, but such a regular expression does not have any "
        errMsg += "match within the target URL page content, please provide "
        errMsg += "another regular expression."
        logger.error(errMsg)

        return False

def checkNullConnection():
    """
    Reference: http://www.wisec.it/sectou.php?id=472f952d79293
    """

    infoMsg = "testing NULL connection to the target url"
    logger.info(infoMsg)

    try:
        page, headers = Request.getPage(method="HEAD")
        if not page and 'Content-Length' in headers:
            kb.nullConnection = "HEAD"

            infoMsg = "NULL connection is supported with HEAD header"
            logger.info(infoMsg)
        else:
            page, headers = Request.getPage(auxHeaders={"Range":"bytes=-1"})
            if page and len(page) == 1 and 'Content-Range' in headers:
                kb.nullConnection = "Range"

                infoMsg = "NULL connection is supported with GET header "
                infoMsg += "'%s'" % kb.nullConnection
                logger.info(infoMsg)
    except sqlmapConnectionException, errMsg:
        errMsg = getUnicode(errMsg)
        raise sqlmapConnectionException, errMsg

    return kb.nullConnection is not None

def checkConnection():
    try:
        socket.gethostbyname(conf.hostname)
    except socket.gaierror:
        errMsg = "host '%s' does not exist" % conf.hostname
        raise sqlmapConnectionException, errMsg

    infoMsg = "testing connection to the target url"
    logger.info(infoMsg)

    try:
        page, _ = Request.getPage()
        conf.seqMatcher.set_seq1(page if not conf.textOnly else getFilteredPageContent(page))

    except sqlmapConnectionException, errMsg:
        errMsg = getUnicode(errMsg)
        raise sqlmapConnectionException, errMsg

    return True
