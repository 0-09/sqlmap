#!/usr/bin/env python

"""
Copyright (c) 2006-2012 sqlmap developers (http://www.sqlmap.org/)
See the file 'doc/COPYING' for copying permission
"""

import logging
import sys

from extra.ansistrm.ansistrm import ColorizingStreamHandler
from lib.core.enums import CUSTOM_LOGGING

# sqlmap logger
logging.addLevelName(CUSTOM_LOGGING.PAYLOAD, "PAYLOAD")
logging.addLevelName(CUSTOM_LOGGING.TRAFFIC_OUT, "TRAFFIC OUT")
logging.addLevelName(CUSTOM_LOGGING.TRAFFIC_IN, "TRAFFIC IN")

LOGGER = logging.getLogger("sqlmapLog")

LEVEL_COLORS = {
                    "CRITICAL": "white",
                    "ERROR": "red",
                    "WARNING": "yellow",
                    "INFO": "green",
                    "DEBUG": "blue",
                    "PAYLOAD": "magenta",
                    "TRAFFIC OUT": "cyan",
                    "TRAFFIC IN": "grey"
               }

LEVEL_ON_COLORS = {
                    "CRITICAL": "on_red",
                  }

LEVEL_ATTRS = {
                "CRITICAL": ('bold',),
              }


try:
    import ctypes
    LOGGER_HANDLER = ColorizingStreamHandler(sys.stdout)
except ImportError:
    LOGGER_HANDLER = logging.StreamHandler(sys.stdout)

FORMATTER = logging.Formatter("\r[%(asctime)s] [%(levelname)s] %(message)s", "%H:%M:%S")

LOGGER_HANDLER.setFormatter(FORMATTER)
LOGGER.addHandler(LOGGER_HANDLER)
LOGGER.setLevel(logging.WARN)
