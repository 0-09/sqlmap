#!/usr/bin/env python

"""
$Id$

Copyright (c) 2006-2010 sqlmap developers (http://sqlmap.sourceforge.net/)
See the file 'doc/COPYING' for copying permission
"""

import re

from lib.core.agent import agent
from lib.core.common import backend
from lib.core.common import format
from lib.core.data import conf
from lib.core.data import kb
from lib.core.data import logger
from lib.core.enums import DBMS
from lib.core.session import setDbms
from lib.core.settings import ORACLE_ALIASES
from lib.request import inject
from lib.request.connect import Connect as Request

from plugins.generic.fingerprint import Fingerprint as GenericFingerprint

class Fingerprint(GenericFingerprint):
    def __init__(self):
        GenericFingerprint.__init__(self, DBMS.ORACLE)

    def getFingerprint(self):
        value  = ""
        wsOsFp = format.getOs("web server", kb.headersFp)

        if wsOsFp:
            value += "%s\n" % wsOsFp

        if kb.data.banner:
            dbmsOsFp = format.getOs("back-end DBMS", kb.bannerFp)

            if dbmsOsFp:
                value += "%s\n" % dbmsOsFp

        value += "back-end DBMS: "

        if not conf.extensiveFp:
            value += DBMS.ORACLE
            return value

        actVer      = format.getDbms()
        blank       = " " * 15
        value      += "active fingerprint: %s" % actVer

        if kb.bannerFp:
            banVer = kb.bannerFp["dbmsVersion"] if 'dbmsVersion' in kb.bannerFp else None
            banVer = format.getDbms([banVer])
            value += "\n%sbanner parsing fingerprint: %s" % (blank, banVer)

        htmlErrorFp = format.getErrorParsedDBMSes()

        if htmlErrorFp:
            value += "\n%shtml error message fingerprint: %s" % (blank, htmlErrorFp)

        return value

    def checkDbms(self):
        if not conf.extensiveFp and (backend.isDbmsWithin(ORACLE_ALIASES) or conf.dbms in ORACLE_ALIASES):
            setDbms(DBMS.ORACLE)

            self.getBanner()

            return True

        logMsg = "testing %s" % DBMS.ORACLE
        logger.info(logMsg)

        # NOTE: SELECT ROWNUM=ROWNUM FROM DUAL does not work connecting
        # directly to the Oracle database
        if conf.direct:
            result = True
        else:
            result = inject.checkBooleanExpression("ROWNUM=ROWNUM")

        if result:
            logMsg = "confirming %s" % DBMS.ORACLE
            logger.info(logMsg)

            # NOTE: SELECT LENGTH(SYSDATE)=LENGTH(SYSDATE) FROM DUAL does
            # not work connecting directly to the Oracle database
            if conf.direct:
                result = True
            else:
                result = inject.checkBooleanExpression("LENGTH(SYSDATE)=LENGTH(SYSDATE)")

            if not result:
                warnMsg = "the back-end DBMS is not %s" % DBMS.ORACLE
                logger.warn(warnMsg)

                return False

            setDbms(DBMS.ORACLE)

            self.getBanner()

            if not conf.extensiveFp:
                return True

            infoMsg = "actively fingerprinting %s" % DBMS.ORACLE
            logger.info(infoMsg)

            for version in ("11i", "10g", "9i", "8i"):
                number = int(re.search("([\d]+)", version).group(1))
                output = inject.checkBooleanExpression("%d=(SELECT SUBSTR((VERSION), 1, %d) FROM SYS.PRODUCT_COMPONENT_VERSION WHERE ROWNUM=1)" % (number, 1 if number < 10 else 2))

                if output:
                    backend.setVersion(version)
                    break

            return True
        else:
            warnMsg = "the back-end DBMS is not %s" % DBMS.ORACLE
            logger.warn(warnMsg)

            return False

    def forceDbmsEnum(self):
        if conf.db:
            conf.db = conf.db.upper()
        else:
            conf.db = "USERS"

            warnMsg  = "on %s it is only possible to enumerate " % DBMS.ORACLE
            warnMsg += "if you provide a TABLESPACE_NAME as database "
            warnMsg += "name. sqlmap is going to use 'USERS' as database "
            warnMsg += "name"
            logger.warn(warnMsg)

        if conf.tbl:
            conf.tbl = conf.tbl.upper()
