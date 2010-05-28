#!/usr/bin/env python

"""
$Id$

This file is part of the sqlmap project, http://sqlmap.sourceforge.net.

Copyright (c) 2007-2010 Bernardo Damele A. G. <bernardo.damele@gmail.com>
Copyright (c) 2006 Daniele Bellucci <daniele.bellucci@gmail.com>

sqlmap is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free
Software Foundation version 2 of the License.

sqlmap is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
details.

You should have received a copy of the GNU General Public License along
with sqlmap; if not, write to the Free Software Foundation, Inc., 51
Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""

from lib.core.agent import agent
from lib.core.common import dataToSessionFile
from lib.core.convert import base64pickle
from lib.core.convert import base64unpickle
from lib.core.data import conf
from lib.core.data import kb
from lib.core.data import logger
from lib.core.settings import SQL_STATEMENTS
from lib.utils.timeout import timeout

def direct(query, content=True):
    output = None
    select = False
    query = agent.payloadDirect(query)

    if kb.dbms == "Oracle" and query.startswith("SELECT ") and " FROM " not in query:
        query = "%s FROM DUAL" % query

    for sqlTitle, sqlStatements in SQL_STATEMENTS.items():
        for sqlStatement in sqlStatements:
            if query.lower().startswith(sqlStatement) and sqlTitle == "SQL SELECT statement":
                select = True
                break

    logger.log(9, query)

    if not select:
        output = timeout(func=conf.dbmsConnector.execute, args=(query,), duration=conf.timeout, default=None)
    elif conf.hostname in kb.resumedQueries and query in kb.resumedQueries[conf.hostname] and "sqlmapoutput" not in query and "sqlmapfile" not in query:
        output = base64unpickle(kb.resumedQueries[conf.hostname][query][:-1])

        infoMsg  = "resumed from file '%s': " % conf.sessionFile
        infoMsg += "%s..." % unicode(output)[:20]
        logger.info(infoMsg)
    elif select:
        output = timeout(func=conf.dbmsConnector.select, args=(query,), duration=conf.timeout, default=None)

    if output is None or len(output) == 0:
        return None
    elif content:
        if conf.hostname not in kb.resumedQueries or ( conf.hostname in kb.resumedQueries and query not in kb.resumedQueries[conf.hostname] ):
            dataToSessionFile("[%s][%s][%s][%s][%s]\n" % (conf.hostname, kb.injPlace, conf.parameters[kb.injPlace], query, base64pickle(output)))

        if len(output) == 1:
            if len(output[0]) == 1:
                return unicode(list(output)[0][0])
            else:
                return list(output)
        else:
            return output
    else:
        for line in output:
            if line[0] in (1, -1):
                return True
            else:
                return False
