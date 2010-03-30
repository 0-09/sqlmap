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

from lib.core.data import conf
from lib.core.data import kb
from lib.core.data import logger
from lib.core.settings import MSSQL_ALIASES
from lib.core.settings import MYSQL_ALIASES
from lib.core.settings import ORACLE_ALIASES
from lib.core.settings import PGSQL_ALIASES
from lib.core.settings import SQLITE_ALIASES
from lib.core.settings import ACCESS_ALIASES
from lib.core.settings import FIREBIRD_ALIASES

from plugins.dbms.mssqlserver import MSSQLServerMap
from plugins.dbms.mssqlserver.connector import Connector as MSSQLServerConn
from plugins.dbms.mysql import MySQLMap
from plugins.dbms.mysql.connector import Connector as MySQLConn
from plugins.dbms.oracle import OracleMap
from plugins.dbms.oracle.connector import Connector as OracleConn
from plugins.dbms.postgresql import PostgreSQLMap
from plugins.dbms.postgresql.connector import Connector as PostgreSQLConn
from plugins.dbms.sqlite import SQLiteMap
from plugins.dbms.sqlite.connector import Connector as SQLiteConn
from plugins.dbms.access import AccessMap
from plugins.dbms.access.connector import Connector as AccessConn
from plugins.dbms.firebird import FirebirdMap
from plugins.dbms.firebird.connector import Connector as FirebirdConn

def setHandler():
    """
    Detect which is the target web application back-end database
    management system.
    """

    count     = 0
    dbmsNames = ( "MySQL", "Oracle", "PostgreSQL", "Microsoft SQL Server", "SQLite", "Microsoft Access", "Firebird" )
    dbmsMap   = (
                  ( MYSQL_ALIASES, MySQLMap, MySQLConn ),
                  ( ORACLE_ALIASES, OracleMap, OracleConn ),
                  ( PGSQL_ALIASES, PostgreSQLMap, PostgreSQLConn ),
                  ( MSSQL_ALIASES, MSSQLServerMap, MSSQLServerConn ),
                  ( SQLITE_ALIASES, SQLiteMap, SQLiteConn ),
                  ( ACCESS_ALIASES, AccessMap, AccessConn ),
                  ( FIREBIRD_ALIASES, FirebirdMap, FirebirdConn ),
                )

    for dbmsAliases, dbmsMap, dbmsConn in dbmsMap:
        if conf.dbms and conf.dbms not in dbmsAliases:
            debugMsg  = "skipping test for %s" % dbmsNames[count]
            logger.debug(debugMsg)

            count += 1

            continue

        handler = dbmsMap()
        conf.dbmsConnector = dbmsConn()
        
        if conf.direct:
            conf.dbmsConnector.connect()

        if handler.checkDbms():
            if not conf.dbms or conf.dbms in dbmsAliases:
                kb.dbmsDetected = True

                conf.dbmsHandler = handler

                return
        else:
            conf.dbmsConnector = None
