"""Utility functions and constructs
"""
import hashlib
import logging
import sys
import socket
from contextlib import closing

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

def getFreePort():
    
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]
