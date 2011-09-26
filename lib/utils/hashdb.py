#!/usr/bin/env python

"""
$Id$

Copyright (c) 2006-2011 sqlmap developers (http://www.sqlmap.org/)
See the file 'doc/COPYING' for copying permission
"""

import hashlib
import sqlite3

from lib.core.settings import UNICODE_ENCODING
from lib.core.threads import getCurrentThreadData

class HashDB(object):
    def __init__(self, filepath):
        self.filepath = filepath

    def _get_cursor(self):
        threadData = getCurrentThreadData()

        if threadData.hashDBCursor is None:
            connection = sqlite3.connect(self.filepath, isolation_level=None)
            threadData.hashDBCursor = connection.cursor()
            threadData.hashDBCursor.execute("CREATE TABLE IF NOT EXISTS storage (id INTEGER PRIMARY KEY, value TEXT)")

        return threadData.hashDBCursor

    cursor = property(_get_cursor)

    def __del__(self):
        self.close()

    def close(self):
        try:
            self.endTransaction()
            self.cursor.connection.close()
        except:
            pass

    def hashKey(self, key):
        key = key.encode(UNICODE_ENCODING) if isinstance(key, unicode) else repr(key)
        retVal = int(hashlib.md5(key).hexdigest()[:8], 16)
        return retVal

    def retrieve(self, key):
        retVal = None
        if key:
            hash_ = self.hashKey(key)
            for row in self.cursor.execute("SELECT value FROM storage WHERE id=?", (hash_,)):
                retVal = row[0]
        return retVal

    def write(self, key, value):
        if key:
            hash_ = self.hashKey(key)
            try:
                self.cursor.execute("INSERT INTO storage VALUES (?, ?)", (hash_, value,))
            except sqlite3.IntegrityError:
                self.cursor.execute("UPDATE storage SET value=? WHERE id=?", (value, hash_,))
