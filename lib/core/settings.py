#!/usr/bin/env python

"""
$Id$

Copyright (c) 2006-2010 sqlmap developers (http://sqlmap.sourceforge.net/)
See the file 'doc/COPYING' for copying permission
"""

import logging
import os
import subprocess
import sys

from lib.core.enums import DBMS
from lib.core.revision import getRevisionNumber

# sqlmap version and site
VERSION            = "0.9-dev"
REVISION           = getRevisionNumber()
VERSION_STRING     = "sqlmap/%s" % VERSION
DESCRIPTION        = "automatic SQL injection and database takeover tool"
SITE               = "http://sqlmap.sourceforge.net"

# minimum distance of ratio from kb.matchRatio to result in True
DIFF_TOLERANCE     = 0.05
CONSTANT_RATIO     = 0.9

# lower and upper values for match ratio in case of stable page
LOWER_RATIO_BOUND = 0.02
UPPER_RATIO_BOUND = 0.98

# sqlmap logger
logging.addLevelName(9, "PAYLOAD")
logging.addLevelName(8, "TRAFFIC OUT")
logging.addLevelName(7, "TRAFFIC IN")

LOGGER             = logging.getLogger("sqlmapLog")
LOGGER_HANDLER     = logging.StreamHandler(sys.stdout)
FORMATTER          = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%H:%M:%S")

LOGGER_HANDLER.setFormatter(FORMATTER)
LOGGER.addHandler(LOGGER_HANDLER)
LOGGER.setLevel(logging.WARN)

# dump markers
DUMP_NEWLINE_MARKER = "__NEWLINE__"
DUMP_CR_MARKER      = "__CARRIAGE_RETURN__"
DUMP_DEL_MARKER     = "__DEL__"
DUMP_TAB_MARKER     = "__TAB__"
DUMP_START_MARKER   = "__START__"
DUMP_STOP_MARKER    = "__STOP__"

PAYLOAD_DELIMITER   = "\x00"
CHAR_INFERENCE_MARK = "%c"
NON_CONTROL_CHAR_REGEX = r'[^\x00-\x1f]'

# coefficient used for a time-based query delay checking (must be >= 7)
TIME_STDEV_COEFF = 10

# length of queue for candidates for time delay adjustment
TIME_DELAY_CANDIDATES = 3

# default time delay in seconds
TIME_DEFAULT_DELAY = 5

# maximum number of techniques used in inject.py/getValue() per one value
MAX_TECHNIQUES_PER_VALUE = 2

# suffix used for naming meta databases in DBMS(es) without explicit database name
METADB_SUFFIX = "_masterdb"

# minimum time response set needed for time-comparison based on standard deviation
MIN_TIME_RESPONSES = 15

# after these number of blanks at the end inference should stop (just in case)
INFERENCE_BLANK_BREAK = 10

# string used for representation of unknown dbms version
UNKNOWN_DBMS_VERSION = "Unknown"

# dynamicity mark length used in dynamicity removal engine
DYNAMICITY_MARK_LENGTH = 32

# dummy user prefix used in dictionary attack
DUMMY_USER_PREFIX = '__dummy__'

# System variables
IS_WIN             = subprocess.mswindows
# The name of the operating system dependent module imported. The following
# names have currently been registered: 'posix', 'nt', 'mac', 'os2', 'ce',
# 'java', 'riscos'
PLATFORM           = os.name
PYVERSION          = sys.version.split()[0]

# Url to update Microsoft SQL Server XML versions file from
MSSQL_VERSIONS_URL = "http://www.sqlsecurity.com/FAQs/SQLServerVersionDatabase/tabid/63/Default.aspx"

# Database management system specific variables
MSSQL_SYSTEM_DBS    = ( "Northwind", "model", "msdb", "pubs", "tempdb" )
MYSQL_SYSTEM_DBS    = ( "information_schema", "mysql" )                   # Before MySQL 5.0 only "mysql"
PGSQL_SYSTEM_DBS    = ( "information_schema", "pg_catalog", "pg_toast" )
ORACLE_SYSTEM_DBS   = ( "SYSTEM", "SYSAUX" )                              # These are TABLESPACE_NAME
SQLITE_SYSTEM_DBS   = ( "sqlite_master", "sqlite_temp_master" )
ACCESS_SYSTEM_DBS   = ( "MSysAccessObjects", "MSysACEs", "MSysObjects", "MSysQueries", "MSysRelationships", "MSysAccessStorage",\
                        "MSysAccessXML", "MSysModules", "MSysModules2" )
FIREBIRD_SYSTEM_DBS = ( "RDB$BACKUP_HISTORY", "RDB$CHARACTER_SETS", "RDB$CHECK_CONSTRAINTS", "RDB$COLLATIONS", "RDB$DATABASE",\
                        "RDB$DEPENDENCIES", "RDB$EXCEPTIONS", "RDB$FIELDS", "RDB$FIELD_DIMENSIONS", " RDB$FILES", "RDB$FILTERS",\
                        "RDB$FORMATS", "RDB$FUNCTIONS", "RDB$FUNCTION_ARGUMENTS", "RDB$GENERATORS", "RDB$INDEX_SEGMENTS", "RDB$INDICES",\
                        "RDB$LOG_FILES", "RDB$PAGES", "RDB$PROCEDURES", "RDB$PROCEDURE_PARAMETERS", "RDB$REF_CONSTRAINTS", "RDB$RELATIONS",\
                        "RDB$RELATION_CONSTRAINTS", "RDB$RELATION_FIELDS", "RDB$ROLES", "RDB$SECURITY_CLASSES", "RDB$TRANSACTIONS", "RDB$TRIGGERS",\
                        "RDB$TRIGGER_MESSAGES", "RDB$TYPES", "RDB$USER_PRIVILEGES", "RDB$VIEW_RELATIONS" )
MAXDB_SYSTEM_DBS    = ( "SYSINFO", "DOMAIN" )
SYBASE_SYSTEM_DBS   = ( "master", "model", "sybsystemdb", "sybsystemprocs" )

MSSQL_ALIASES       = [ "microsoft sql server", "mssqlserver", "mssql", "ms" ]
MYSQL_ALIASES       = [ "mysql", "my" ]
PGSQL_ALIASES       = [ "postgresql", "postgres", "pgsql", "psql", "pg" ]
ORACLE_ALIASES      = [ "oracle", "orcl", "ora", "or" ]
SQLITE_ALIASES      = [ "sqlite", "sqlite3" ]
ACCESS_ALIASES      = [ "access", "jet", "microsoft access", "msaccess" ]
FIREBIRD_ALIASES    = [ "firebird", "mozilla firebird", "interbase", "ibase", "fb" ]
MAXDB_ALIASES       = [ "maxdb", "sap maxdb", "sap db" ]
SYBASE_ALIASES      = [ "sybase", "sybase sql server" ]

SUPPORTED_DBMS      = MSSQL_ALIASES + MYSQL_ALIASES + PGSQL_ALIASES + ORACLE_ALIASES + SQLITE_ALIASES + ACCESS_ALIASES + FIREBIRD_ALIASES + MAXDB_ALIASES + SYBASE_ALIASES
SUPPORTED_OS        = ( "linux", "windows" )

INBAND_FROM_TABLE   = {DBMS.ORACLE: " FROM DUAL", DBMS.ACCESS: " FROM MSysObjects", DBMS.FIREBIRD: " FROM RDB$DATABASE", DBMS.MAXDB: " FROM VERSIONS"}

SQL_STATEMENTS      = {
                       "SQL SELECT statement":  (
                             "select ",
                             "show ",
                             " top ",
                             " distinct ",
                             " from ",
                             " from dual",
                             " where ",
                             " group by ",
                             " order by ",
                             " having ",
                             " limit ",
                             " offset ",
                             " union all ",
                             " rownum as ",
                             "(case ",         ),

                       "SQL data definition":   (
                             "create ",
                             "declare ",
                             "drop ",
                             "truncate ",
                             "alter ",         ),

                       "SQL data manipulation": (
                             "insert ",
                             "update ",
                             "delete ",
                             "merge ",         ),

                       "SQL data control":      (
                             "grant ",         ),

                       "SQL data execution":    (
                             " exec ",
                             "execute ",       ),

                       "SQL transaction":       (
                             "start transaction ",
                             "begin work ",
                             "begin transaction ",
                             "commit ",
                             "rollback ",      ),
                     }

ERROR_PARSING_REGEXES = (   
                          r"<b>[^<]*(fatal|error|warning|exception)[^<]*</b>:?\s*(?P<result>.+?)<br\s*/?\s*>", 
                          r"<li>Error Type:<br>(?P<result>.+?)</li>", 
                          r"error '[0-9a-f]{8}'((<[^>]+>)|\s)+(?P<result>[^<>]+)"
                        )

META_CHARSET_REGEX  = r'<meta http-equiv="?content-type"?[^>]+charset=(?P<result>[^">]+)'

# Reference: http://www.cs.ru.nl/bachelorscripties/2010/Martin_Devillers___0437999___Analyzing_password_strength.pdf
COMMON_PASSWORD_SUFFIXES = ["1", "123", "2", "12", "3", "13", "7", "11", "5", "22", "23", "01", "4", "07", "21", "14", "10", "06", "08", "8", "15", "69", "16", "6", "18"]

# Reference: http://www.the-interweb.com/serendipity/index.php?/archives/94-A-brief-analysis-of-40,000-leaked-MySpace-passwords.html
COMMON_PASSWORD_SUFFIXES += ["!", ".", "*", "!!", "?", ";", "..", "!!!", ",", "@"]
