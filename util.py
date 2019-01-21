"""Utility functions and constructs
"""
import hashlib
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

def hashAlgo(algoCode, hashmethod='SHA256'):
    logger.info(algoCode)
    algoCode = algoCode.encode('utf-8')
    h = hashlib.new(hashmethod)
    h.update(algoCode)
    return h.hexdigest()

def getLogger(filename):
    pass

def compose(*funcs):
    pass
