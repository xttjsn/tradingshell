"""Wrapper for any unbound / partially bounded functions
"""
from functools import partial
import inspect
import logging
import sys
import copy

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

class UnboundAction(object):

    def __init__(self, f, *args, **kwargs):
        self._partial_f = partial(f, *args, **kwargs)

    def __call__(self, **kwargs):
        f_args = inspect.getargspec(self._partial_f).args or []
        defaults = inspect.getargspec(self._partial_f).defaults or []
        f_args = [item for item in f_args if item != 'self']

        logger.info('f_args:{}'.format(f_args))
        logger.info('defaults:{}'.format(defaults))
        
        res_args = []
        for idx, key in enumerate(f_args):
            if key not in kwargs:
                logger.error('{} not found in kwargs'.format(key))
                raise KeyError('{} not found in kwargs'.format(key))
            if idx < len(f_args) - len(defaults):  # Meaning it's non-keyword-argument
                res_args.append(kwargs[key])
                del kwargs[key]

        keys = list(kwargs.keys())
        for key in keys:
            if key not in f_args:
                del kwargs[key]

        return self._partial_f(*(tuple(res_args)), **kwargs)
