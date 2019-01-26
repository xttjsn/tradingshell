"""Wrapper for any unbound / partially bounded functions
"""
from functools import partial
import inspect
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

class UnboundAction(object):

    def __init__(self, f, *args, **kwargs):
        self._partial_f = partial(f, *args, **kwargs)

    def __call__(self, **kwargs):
        f_args = inspect.getargspec(self._partial_f).args or []
        defaults = inspect.getargspec(self._partial_f).defaults or []
        f_args = [item for item in f_args if item != 'self']

        logger.info(f'f_args:{f_args}')
        logger.info(f'defaults:{defaults}')
        
        res_args = []
        for idx, key in enumerate(f_args):
            if key not in kwargs:
                logger.error(f'{key} not found in kwargs')
                raise KeyError(f'{key} not found in kwargs')
            if idx < len(f_args) - len(defaults):  # Meaning it's non-keyword-argument
                res_args.append(kwargs[key])
                del kwargs[key]

        logger.info(f'res_args: {res_args}')
        
        return self._partial_f(*(tuple(res_args)), **kwargs)
