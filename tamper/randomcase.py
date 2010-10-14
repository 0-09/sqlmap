import re
import string

from lib.core.common import randomRange
from lib.core.exception import sqlmapUnsupportedFeatureException

"""
value -> chars from value with random case (e.g., INSERT->InsERt)
"""
#TODO: only do it for deepness = 0 regarding '"
def tamper(place, value):
    retVal = value
    if value:
        retVal = ""
        for i in xrange(len(value)):
            if value[i].isalpha():
                retVal += value[i].upper() if randomRange(0,1) else value[i].lower()
            else:
                retVal += value[i]
    return retVal
