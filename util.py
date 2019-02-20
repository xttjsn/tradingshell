"""Utility functions and constructs
"""
import hashlib
import logging
import sys
import socket, errno
from contextlib import closing

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)


def hashAlgo(algoCode, hashmethod='SHA256'):
    logger.info(algoCode)
    algoCode = algoCode.encode('utf-8')
    h = hashlib.new(hashmethod)
    h.update(algoCode)
    return h.hexdigest()


def getFreePort():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def isFreePort(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('', port))
    except socket.error as e:
        if e.errno == errno.EADDRINUSE:
            s.close()
            return False
        else:
            s.close()
            return True
